import os
import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights
import torchvision.transforms as T
from PIL import Image
import glob

# -------------------------------------------------------------------
# 1. CONFIGURATION
# -------------------------------------------------------------------

MODEL_PATH = "modelis.pth"

# Path to the main folder containing the subfolders
BASE_DIR = "specifiska_teritorija"

# Assuming standard structure: base/reljefs/ and base/slipums/
# If your images are all in one folder, set both of these to BASE_DIR
RELJEFS_DIR = os.path.join(BASE_DIR, "reljefs")
SLIPUMS_DIR = os.path.join(BASE_DIR, "slipums")

IMG_SIZE = 768
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# -------------------------------------------------------------------
# 2. MODEL DEFINITION
# -------------------------------------------------------------------

class HillfortNetV2(nn.Module):
    def __init__(self):
        super().__init__()
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

# -------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# -------------------------------------------------------------------

def load_trained_model(model_path):
    print(f"Loading model from: {model_path} ...")
    model = HillfortNetV2().to(DEVICE)
    
    try:
        checkpoint = torch.load(model_path, map_location=DEVICE)
        if 'model' in checkpoint:
            model.load_state_dict(checkpoint['model'])
        else:
            model.load_state_dict(checkpoint)
        model.eval() # Set to evaluation mode immediately
        return model
    except Exception as e:
        print(f"CRITICAL ERROR loading model: {e}")
        exit()

def process_single_pair(model, r_path, s_path, transform_pipeline):
    """
    Takes paths, loads images, returns probability.
    Returns -1 if images fail to load.
    """
    try:
        img_r = Image.open(r_path).convert("RGB")
        img_s = Image.open(s_path).convert("RGB")
    except Exception as e:
        print(f"Error opening files: {e}")
        return -1

    t_r = transform_pipeline(img_r)
    t_s = transform_pipeline(img_s)

    # Stack to create 6-channel tensor
    combined = torch.cat((t_r, t_s), dim=0)
    input_tensor = combined.unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(input_tensor)
        probability = torch.sigmoid(logits).item()
    
    return probability

# -------------------------------------------------------------------
# 4. MAIN BATCH PROCESS
# -------------------------------------------------------------------

def run_batch_process():
    # 1. Load Model Once
    model = load_trained_model(MODEL_PATH)
    
    # 2. Setup Transforms
    transform_pipeline = T.Compose([
        T.Resize((IMG_SIZE, IMG_SIZE)),
        T.ToTensor(),
        T.Normalize([0.5]*3, [0.5]*3)
    ])

    # 3. Find Files
    # Get all png files in the relief folder
    search_pattern = os.path.join(RELJEFS_DIR, "*reljefs*.png")
    relief_files = glob.glob(search_pattern)
    
    # Sort files to ensure order (e.g., 1, 2, 3...)
    relief_files.sort()

    if not relief_files:
        print(f"No files found in {RELJEFS_DIR}. Check your paths.")
        return

    print(f"\nFound {len(relief_files)} sets of images to process.")
    print(f"{'-'*85}")
    print(f"{'FILENAME (ID)':<40} | {'PROBABILITY':<12} | {'OPINION'}")
    print(f"{'-'*85}")

    # 4. Loop through images
    for r_path in relief_files:
        # Construct the matching Slope path
        # Logic: Replace the folder name 'reljefs' with 'slipums' 
        # AND replace the filename part '_reljefs_' with '_slipums_'
        
        # Example r_path: specifiska_teritorija/reljefs/specifiska_teritorija_reljefs_3.png
        
        filename = os.path.basename(r_path)
        
        # Try to guess the slope filename
        s_filename = filename.replace("reljefs", "slipums")
        s_path = os.path.join(SLIPUMS_DIR, s_filename)

        if not os.path.exists(s_path):
            print(f"{filename:<40} | ERROR        | Missing matching slope file")
            continue

        # Run Prediction
        prob = process_single_pair(model, r_path, s_path, transform_pipeline)

        if prob == -1:
            print(f"{filename:<40} | ERROR        | Image Load Failed")
        else:
            opinion = "YES (Hillfort)" if prob > 0.5 else "NO"
            print(f"{filename:<40} | {prob:.4f}       | {opinion}")

    print(f"{'-'*85}\nDone.")

if __name__ == "__main__":
    run_batch_process()