import sys
import os
import math
import time
import requests
import numpy as np
import cv2
import torch
import torch.nn as nn
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from torchvision.models import resnet18, ResNet18_Weights
from torchvision import transforms
from PIL import Image
from io import BytesIO
from pyproj import Transformer
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QSlider, QGraphicsScene, QGraphicsView, 
                             QGraphicsPixmapItem, QProgressBar, QRadioButton, 
                             QButtonGroup, QToolTip, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QBrush, QCursor, QPen

# ----------------------------------------
# 1. CONFIGURATION
# ----------------------------------------
MODEL_PATH = "best_model_v2.pth"

# Model Input Specs
IMG_SIZE = 768           # Pixels (Model input)
REAL_WORLD_SIZE = 256    # Meters (Real world coverage of the 768px image)

# Grid/Visual Specs
# We step 64 meters at a time to create the map.
# 256m / 64m = 4 steps per full image context (Heavy overlap for better detection)
GRID_STEP_METERS = 64    

# Calculate Visual Tile Size (The center crop used for the GUI map)
# Ratio: 768px / 256m = 3 px/m
# Visual Tile = 64m * 3 px/m = 192px
VISUAL_TILE_SIZE = int(GRID_STEP_METERS * (IMG_SIZE / REAL_WORLD_SIZE))

LAYER_RELIEF = "ZemeLKS"
LAYER_SLOPE = "SlopeLKS"
BG_COLOR = "#122a41"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ----------------------------------------
# 2. MODEL DEFINITION (HillfortNetV2)
# ----------------------------------------
class HillfortNetV2(nn.Module):
    def __init__(self):
        super().__init__()
        # Load ResNet18 with ImageNet weights
        self.base = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)

        # Modify first layer for 6 channels
        old_weights = self.base.conv1.weight
        self.base.conv1 = nn.Conv2d(6, 64, kernel_size=7, stride=2, padding=3, bias=False)

        # Keep original weights for initialization structure
        with torch.no_grad():
            self.base.conv1.weight[:, :3] = old_weights
            self.base.conv1.weight[:, 3:] = old_weights

        # Modify output head
        self.base.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(self.base.fc.in_features, 1)
        )

    def forward(self, x):
        return self.base(x)

def load_trained_model():
    print(f"Loading model from: {MODEL_PATH} ...")
    model = HillfortNetV2().to(DEVICE)
    
    if not os.path.exists(MODEL_PATH):
        print("Model file not found! Please ensure 'best_model_v2.pth' is in the folder.")
        return None

    try:
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
        if 'model' in checkpoint:
            model.load_state_dict(checkpoint['model'])
        else:
            model.load_state_dict(checkpoint)
        model.eval()
        return model
    except Exception as e:
        print(f"CRITICAL ERROR loading model: {e}")
        return None

# ----------------------------------------
# 3. CUSTOM ZOOMABLE VIEWER
# ----------------------------------------
class MapViewer(QGraphicsView):
    """Custom View to handle Zooming and Clicking"""
    click_signal = pyqtSignal(int, int)

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setStyleSheet(f"background-color: {BG_COLOR}; border: none;")
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.click_signal.emit(int(scene_pos.x()), int(scene_pos.y()))

# ----------------------------------------
# 4. SCANNER WORKER
# ----------------------------------------
class ScannerWorker(QThread):
    # Emits (row, col, ReliefImage, SlopeImage, Score)
    tile_ready = pyqtSignal(int, int, object, object, float) 
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    grid_info = pyqtSignal(int, int)

    def __init__(self, lat1, lon1, lat2, lon2):
        super().__init__()
        self.lat1, self.lon1 = lat1, lon1
        self.lat2, self.lon2 = lat2, lon2
        self.is_running = True
        
        # Configure Session
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def is_blank_image(self, pil_img):
        if pil_img is None: return True
        try:
            img_arr = np.array(pil_img)
            std = np.std(img_arr)
            return std < 1.0 
        except:
            return True

    def fetch_layer(self, url, layer_name, bbox):
        full_url = f"{url}&LAYERS=public:{layer_name}&BBOX={bbox}"
        max_attempts = 3
        for attempt in range(max_attempts):
            if not self.is_running: return None
            try:
                resp = self.session.get(full_url, timeout=5)
                if resp.status_code == 200:
                    img = Image.open(BytesIO(resp.content)).convert('RGB')
                    if self.is_blank_image(img):
                        time.sleep(0.5)
                        continue
                    return img
            except Exception:
                pass
        return None

    def run(self):
        model = load_trained_model()
        if not model:
            self.finished.emit()
            return

        # Coordinate Transformation
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3059", always_xy=True)
        x1, y1 = transformer.transform(self.lon1, self.lat1)
        x2, y2 = transformer.transform(self.lon2, self.lat2)
        
        # Determine scanning area bounds
        start_y = max(y1, y2)
        start_x = min(x1, x2)
        total_width = abs(x2 - x1)
        total_height = abs(y1 - y2)
        
        # Calculate grid size based on Grid Step (64m)
        cols = int(math.ceil(total_width / GRID_STEP_METERS))
        rows = int(math.ceil(total_height / GRID_STEP_METERS))
        
        self.grid_info.emit(rows, cols)
        total_tiles = cols * rows
        processed = 0

        # Transforms exactly as in your provided code
        transform_pipeline = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.5]*3, [0.5]*3)
        ])

        # WMS URL - requesting 768x768 pixels
        base_url = f"https://lvmgeoserver.lvm.lv/geoserver/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES=&CRS=EPSG:3059&WIDTH={IMG_SIZE}&HEIGHT={IMG_SIZE}&FORMAT=image/png"

        # BBOX Calculation constant
        # We need a box that is REAL_WORLD_SIZE (256m) wide/high
        half_extent = REAL_WORLD_SIZE / 2.0

        for r in range(rows):
            # Calculate center Y for this step
            curr_y = start_y - (r * GRID_STEP_METERS) - (GRID_STEP_METERS/2)
            
            for c in range(cols):
                if not self.is_running: 
                    self.session.close()
                    return

                # Calculate center X for this step
                curr_x = start_x + (c * GRID_STEP_METERS) + (GRID_STEP_METERS/2)
                
                # Construct BBOX for 256m context
                bbox = f"{curr_y - half_extent},{curr_x - half_extent},{curr_y + half_extent},{curr_x + half_extent}"
                
                pil_rel = self.fetch_layer(base_url, LAYER_RELIEF, bbox)
                pil_slp = self.fetch_layer(base_url, LAYER_SLOPE, bbox)

                if pil_rel and pil_slp:
                    try:
                        # 1. Prepare Tensor (Uses same pipeline as your code)
                        t_r = transform_pipeline(pil_rel)
                        t_s = transform_pipeline(pil_slp)
                        combined = torch.cat((t_r, t_s), dim=0)
                        input_tensor = combined.unsqueeze(0).to(DEVICE)

                        # 2. Prediction
                        with torch.no_grad():
                            logits = model(input_tensor)
                            score = torch.sigmoid(logits).item()
                        
                        # 3. Crop Visual Tile for the GUI Map
                        # We downloaded 768x768, but we only want to display the center 
                        # corresponding to our Grid Step to make a seamless map.
                        cx, cy = IMG_SIZE // 2, IMG_SIZE // 2
                        half_tile = VISUAL_TILE_SIZE // 2
                        box = (cx - half_tile, cy - half_tile, cx + half_tile, cy + half_tile)
                        
                        crop_rel = pil_rel.crop(box)
                        crop_slp = pil_slp.crop(box)
                        
                        self.tile_ready.emit(r, c, crop_rel, crop_slp, score)
                    except Exception as e:
                        print(f"Processing error at {r},{c}: {e}")

                processed += 1
                self.progress.emit(int((processed / total_tiles) * 100))
        
        self.session.close()
        self.finished.emit()

    def stop(self):
        self.is_running = False

# ----------------------------------------
# 5. MAIN APPLICATION
# ----------------------------------------
class HillfortApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hillfort Intelligence Suite (Model V2)")
        self.resize(1300, 950)
        self.setStyleSheet(f"background-color: {BG_COLOR}; color: white;")
        
        # State Data
        self.score_matrix = None
        self.relief_items = []
        self.slope_items = []
        self.heatmap_item = None
        self.red_alert_item = None
        self.rows = 0
        self.cols = 0
        
        self.init_ui()
        
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # --- Top Controls ---
        top_bar = QHBoxLayout()
        
        # Coords
        self.in_lat1 = QLineEdit("57.15")
        self.in_lon1 = QLineEdit("25.57")
        self.in_lat2 = QLineEdit("57.14")
        self.in_lon2 = QLineEdit("25.59")
        for w in [self.in_lat1, self.in_lon1, self.in_lat2, self.in_lon2]:
            w.setStyleSheet("background-color: #1e3b52; border: 1px solid #4a6fa5; padding: 4px; color: white;")
        
        top_bar.addWidget(QLabel("TL Lat:"))
        top_bar.addWidget(self.in_lat1)
        top_bar.addWidget(QLabel("TL Lon:"))
        top_bar.addWidget(self.in_lon1)
        top_bar.addWidget(QLabel("BR Lat:"))
        top_bar.addWidget(self.in_lat2)
        top_bar.addWidget(QLabel("BR Lon:"))
        top_bar.addWidget(self.in_lon2)
        
        self.btn_scan = QPushButton(" SCAN REGION ")
        self.btn_scan.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        self.btn_scan.clicked.connect(self.start_scan)
        top_bar.addWidget(self.btn_scan)
        
        layout.addLayout(top_bar)
        
        # --- Layer Controls ---
        layer_bar = QHBoxLayout()
        
        self.rb_relief = QRadioButton("Relief Map")
        self.rb_slope = QRadioButton("Slope Map")
        self.rb_relief.setChecked(True)
        self.rb_relief.toggled.connect(self.toggle_map_layer)
        
        layer_bar.addWidget(QLabel("Base Layer:"))
        layer_bar.addWidget(self.rb_relief)
        layer_bar.addWidget(self.rb_slope)
        
        layer_bar.addSpacing(20)
        self.chk_red_alert = QCheckBox("Red Alert Mode (>85%)")
        self.chk_red_alert.setStyleSheet("""
            QCheckBox { font-weight: bold; color: #ff6347; }
            QCheckBox::indicator:checked { background-color: #ff6347; border: 1px solid white; }
        """)
        self.chk_red_alert.toggled.connect(self.toggle_red_alert)
        self.chk_red_alert.setEnabled(False)
        layer_bar.addWidget(self.chk_red_alert)

        layer_bar.addSpacing(20)
        layer_bar.addWidget(QLabel("Opacity:"))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.update_opacity)
        self.slider.setEnabled(False)
        layer_bar.addWidget(self.slider)
        
        layout.addLayout(layer_bar)
        
        # --- Viewer ---
        self.progress = QProgressBar()
        self.progress.setStyleSheet("QProgressBar {border: 1px solid #4a6fa5; border-radius: 5px; text-align: center;} QProgressBar::chunk {background-color: #2196F3;}")
        
        self.scene = QGraphicsScene()
        self.view = MapViewer(self.scene)
        self.view.click_signal.connect(self.handle_map_click)

        layout.addWidget(self.progress)
        layout.addWidget(self.view)

    def start_scan(self):
        self.scene.clear()
        self.score_matrix = None
        self.heatmap_item = None
        self.red_alert_item = None
        self.relief_items = []
        self.slope_items = []
        
        try:
            l1, lo1 = float(self.in_lat1.text()), float(self.in_lon1.text())
            l2, lo2 = float(self.in_lat2.text()), float(self.in_lon2.text())
        except: return

        self.btn_scan.setEnabled(False)
        self.slider.setEnabled(False)
        self.chk_red_alert.setEnabled(False)
        self.progress.setValue(0)
        
        self.worker = ScannerWorker(l1, lo1, l2, lo2)
        self.worker.grid_info.connect(self.init_grid)
        self.worker.tile_ready.connect(self.add_tile)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()

    def init_grid(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.score_matrix = np.zeros((rows, cols), dtype=np.float32)
        self.relief_items = [None] * (rows * cols)
        self.slope_items = [None] * (rows * cols)

    def add_tile(self, row, col, img_rel, img_slp, score):
        idx = row * self.cols + col
        
        # 1. Create Relief Item
        pix_rel = self.pil2pixmap(img_rel)
        item_rel = QGraphicsPixmapItem(pix_rel)
        item_rel.setPos(col * VISUAL_TILE_SIZE, row * VISUAL_TILE_SIZE)
        self.scene.addItem(item_rel)
        self.relief_items[idx] = item_rel
        
        # 2. Create Slope Item (Hidden by default)
        pix_slp = self.pil2pixmap(img_slp)
        item_slp = QGraphicsPixmapItem(pix_slp)
        item_slp.setPos(col * VISUAL_TILE_SIZE, row * VISUAL_TILE_SIZE)
        item_slp.setVisible(False)
        self.scene.addItem(item_slp)
        self.slope_items[idx] = item_slp
        
        # Store Score
        if self.score_matrix is not None:
            self.score_matrix[row, col] = score

    def on_scan_finished(self):
        self.btn_scan.setEnabled(True)
        self.generate_overlays()

    def generate_overlays(self):
        if self.score_matrix is None: return

        map_h = self.rows * VISUAL_TILE_SIZE
        map_w = self.cols * VISUAL_TILE_SIZE
        
        # --- 1. Standard Heatmap ---
        # Resize grid to full resolution
        upscaled = cv2.resize(self.score_matrix, (map_w, map_h), interpolation=cv2.INTER_CUBIC)
        
        # Blur to smooth transitions
        blur_k = 101
        blurred = cv2.GaussianBlur(upscaled, (blur_k, blur_k), 0)

        # --- THE FIX: Clip to 0.0 - 1.0 ---
        # This prevents "overshoot" values (like 1.1) from wrapping around to 0
        blurred = np.clip(blurred, 0.0, 1.0)
        
        # Generate Grayscale Map (White=Safe, Black=Hillfort)
        grayscale_map = (255 * (1 - blurred)).astype(np.uint8)
        rgb_layer = cv2.cvtColor(grayscale_map, cv2.COLOR_GRAY2RGB)
        
        pix_overlay = self.cv2pixmap(rgb_layer)
        self.heatmap_item = QGraphicsPixmapItem(pix_overlay)
        self.heatmap_item.setZValue(10)
        self.heatmap_item.setOpacity(0.5)
        self.scene.addItem(self.heatmap_item)
        
        # --- 2. Red Alert Overlay ---
        red_overlay_rgba = np.zeros((map_h, map_w, 4), dtype=np.uint8)
        mask = blurred > 0.85
        red_overlay_rgba[mask] = [71, 99, 255, 180] # BGRA: Tomato Red
        
        pix_red = self.cv2pixmap(red_overlay_rgba, is_rgba=True)
        self.red_alert_item = QGraphicsPixmapItem(pix_red)
        self.red_alert_item.setZValue(20)
        self.red_alert_item.setVisible(False)
        self.scene.addItem(self.red_alert_item)
        
        # Enable Controls
        self.slider.setValue(50)
        self.slider.setEnabled(True)
        self.chk_red_alert.setEnabled(True)
        print("Overlays Generated.")

    def toggle_map_layer(self):
        show_relief = self.rb_relief.isChecked()
        for item in self.relief_items:
            if item: item.setVisible(show_relief)
        for item in self.slope_items:
            if item: item.setVisible(not show_relief)

    def toggle_red_alert(self):
        is_red = self.chk_red_alert.isChecked()
        if self.red_alert_item:
            self.red_alert_item.setVisible(is_red)
        if self.heatmap_item:
            self.heatmap_item.setVisible(not is_red)
            self.slider.setEnabled(not is_red)

    def update_opacity(self, value):
        if self.heatmap_item:
            self.heatmap_item.setOpacity(value / 100.0)
            
    def handle_map_click(self, x, y):
        if self.score_matrix is None: return
        
        col = int(x / VISUAL_TILE_SIZE)
        row = int(y / VISUAL_TILE_SIZE)
        
        if 0 <= row < self.rows and 0 <= col < self.cols:
            score = self.score_matrix[row, col]
            percentage = score * 100
            color_hex = "#ff6347" if score > 0.85 else "#ffffff"
            
            QToolTip.showText(
                QCursor.pos(), 
                f"<div style='background-color:#222; color:{color_hex}; padding:5px; font-size:14px; font-weight:bold;'>"
                f"Hillfort Confidence: {percentage:.2f}%</div>"
            )

    # --- Helpers ---
    def pil2pixmap(self, pil_img):
        im_data = pil_img.convert("RGBA").tobytes("raw", "RGBA")
        qim = QImage(im_data, pil_img.size[0], pil_img.size[1], QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qim)
        
    def cv2pixmap(self, cv_img, is_rgba=False):
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        fmt = QImage.Format.Format_RGBA8888 if is_rgba else QImage.Format.Format_RGB888
        q_img = QImage(cv_img.data, w, h, bytes_per_line, fmt)
        return QPixmap.fromImage(q_img)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HillfortApp()
    window.show()
    sys.exit(app.exec())