# -------------------------------------------------------------------------------------------------------------------------------------
#
# Programma veidota zinātniski pētnieciskā darba ietvaros, lai vizualizētu algoritma datu kopas izvēlētos datus. Tā iegūst jau 
# definētās datu koordinātas un attēlo tās virs Latvijas teritorijas robežām.
#
# Programmu veidoja: Roberts Kamarūts
#
# -------------------------------------------------------------------
#
# This program was developed as part of a scientific research paper to visualise selected data from the algorithm's dataset. It fetches 
# already defined data coordinates and plots them over the borders of the Latvian territory.
#
# Program created by: Roberts Kamarūts
#
# -------------------------------------------------------------------------------------------------------------------------------------

import os
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# Importēt datus no ārējā faila (pieņemot, ka 'regioni.py' atrodas tajā pašā mapē)
from regioni import pilskalni, defined_territory

# ------------------------------------------------------------------------------------------
# 1. KONFIGURĀCIJA UN DATU CEĻI
# ------------------------------------------------------------------------------------------

# Ceļš uz Shapefile failu (jābūt 'Kontura' apakšmapē)
shapefile_path = "Kontura/Territorial_units_LV_1.2m_(2025.07.01.).shp"

# Pārbaudīt, vai fails eksistē
if not os.path.exists(shapefile_path):
    print(f"KĻŪDA: Fails nav atrasts ceļā: {os.path.abspath(shapefile_path)}")
    exit()

# ------------------------------------------------------------------------------------------
# 2. KARTES DATU IELĀDE UN APSTRĀDE
# ------------------------------------------------------------------------------------------

# Ielādēt Latvijas kartes datus
gdf = gpd.read_file(shapefile_path)

# Apvienot iekšējās robežas (novadus), lai iegūtu tikai ārējo valsts kontūru
gdf["country"] = 1 
latvia_contour = gdf.dissolve(by="country")

# ------------------------------------------------------------------------------------------
# 3. ĢEOMETRIJU SAGATAVOŠANA (PUNKTI UN TERITORIJAS)
# ------------------------------------------------------------------------------------------

# Sagatavot pilskalnu punktus (GeoDataFrame)
points_data = []
for name, coords in pilskalni.items():
    lat, lon = coords
    points_data.append({"name": name, "geometry": Point(lon, lat)})

gdf_points = gpd.GeoDataFrame(points_data, crs="EPSG:4326")

# Sagatavot teritoriju taisnstūrus (GeoDataFrame)
territory_data = []
for item in defined_territory:
    tid, lat1, lon1, lat2, lon2 = item
    poly = Polygon([
        (lon1, lat1),
        (lon2, lat1),
        (lon2, lat2),
        (lon1, lat2),
        (lon1, lat1)
    ])
    territory_data.append({"id": tid, "geometry": poly})

gdf_territories = gpd.GeoDataFrame(territory_data, crs="EPSG:4326")

# ------------------------------------------------------------------------------------------
# 4. KOORDINĀTU SISTĒMU SASKAŅOŠANA
# ------------------------------------------------------------------------------------------

# Pārveidot punktus un teritorijas uz to pašu projekciju, kas ir kartei
if not latvia_contour.empty:
    target_crs = latvia_contour.crs
    gdf_points = gdf_points.to_crs(target_crs)
    gdf_territories = gdf_territories.to_crs(target_crs)

# ------------------------------------------------------------------------------------------
# 5. VIZUALIZĀCIJA
# ------------------------------------------------------------------------------------------

# Izveidot attēlu (palielināts izmērs)
fig, ax = plt.subplots(figsize=(16, 10))

# 1. Zīmēt Latvijas kontūru
latvia_contour.plot(
    ax=ax, 
    color="white", 
    edgecolor="black", 
    linewidth=1.2,
    zorder=1
)

# 2. Zīmēt definētās teritorijas (solid block, zila krāsa)
gdf_territories.plot(
    ax=ax, 
    color="#122a41",
    alpha=1.0, 
    edgecolor="none",
    zorder=2
)

# 3. Zīmēt pilskalnus (dimanta forma, sarkana krāsa, mazāki)
gdf_points.plot(
    ax=ax, 
    color="red",           
    marker="D",           
    markersize=15,        
    edgecolor="black",    
    linewidth=0.5,
    zorder=3              
)

# 4. Izveidot leģendu kreisajā pusē
legend_elements = [
    Line2D([0], [0], marker="D", color="w", label="Izvēlētie pilskalni",
           markerfacecolor="red", markersize=10, markeredgecolor="black"),
    Patch(facecolor="#122a41", edgecolor="none", label="Izvēlētās parastās teritorijas")
]

# Iestatīt fontu leģendai (Times New Roman) - Palielināts uz 18
legend_font = font_manager.FontProperties(family="Times New Roman", size=18)

# Pievienot leģendu apakšējā KREISAJĀ stūrī
ax.legend(handles=legend_elements, prop=legend_font, loc="lower left", frameon=True)

# Iestatīt virsrakstu ar Times New Roman fontu
#title_font = {"fontname": "Times New Roman", "fontsize": 18}
#ax.set_title("Datu kopā iekļauto pilskalnu un parasto teritoriju ģeotelpiskais izvietojums", **title_font)

# Noformējums (bez asīm)
ax.axis("off")

# Parādīt rezultātu
plt.tight_layout()
plt.show()