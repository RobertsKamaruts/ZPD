# -------------------------------------------------------------------------------------------------------------------------------------
#
# Programma veidota zinātniski pētnieciskā darba ietvaros, lai automatizētu Latvijas reljefa un slīpuma modeļu 
# fotofiksāciju. Lietojot to, var veidot datu kopu, uz kuras tika trenēts pētījumā izstrādātais algoritms.
# 
# Programmas dažādo režīmu koda daļas ir savstarpēji līdzīgas, taču katrā ir nepieciešamas specifiskas nianses to loģikā.
# Tādēļ kopīgās koda daļas nav apvienotas vienā funkcijā. Šajā gadījumā šis ir tehniski vienkāršākais un saprotamākais risinājums.
#
# Programmu veidoja: Roberts Kamarūts
#
# -------------------------------------------------------------------
#
# This program was developed as part of a scientific research paper to automate the image capturing of Latvia's relief and slope models. 
# It enables the generation of the dataset upon which the study's algorithm was trained.
# 
# The code sections for the different modes are similar; however, each requires specific nuances in its logic. Therefore, shared code 
# segments have not been combined into a single function. In this context, this represents the technically simplest and most 
# understandable solution.
#
# Program created by: Roberts Kamarūts
#
# -------------------------------------------------------------------------------------------------------------------------------------

from regioni import pilskalni, defined_territory    # Iegūst definēto pilskalnu un parasto teritoriju koordinātas no regioni.py faila.
from pyproj import Transformer                      # Pārveidos koordinātas no vienas koordinātu sistēmas uz citu.
from colorama import Fore                           # Formatēs tekstu terminālī.
import requests                                     # Iegūs attēlus no WMS servera.
import math                                         # Atļaus apaļot skaitļus.
import os                                           # Darbosies ar mapēm.

# Pamatu iestatījumi.
coordinate_transformer = Transformer.from_crs("EPSG:4326", "EPSG:3059", always_xy=True)     # Pārveidos koordinātas uz LKS-92 metru sistēmu.
image_size = 768                                                                            # Attēlu platums un garums pikseļos.
image_meters = 512                                                                          # Tik daudz metru platumā un garumā reprezentē viens attēls.
increase = 51.2                                                                             # Par tik lielu metru attālumu tiks uzņemts nākamais attēls teritoriju virknē (2. un 3. režīmā).

# Kartes veidi WMS pieprasījuma URL. Šeit ir pieejami dažādi kartes veidi, bet programma lietos tikai divus, lai ietaupītu resursus.
reljefs = "ZemeLKS"
slipums = "SlopeLKS"
#reljefs_linijas = "DTM_contours"
#reljefs_slipums = "SlopeDTM"
#reljefs_slipums_linijas = "SlopeDTM_contours"
#slipums_linijas = "Slope_contours"

# Piefiksē katram kartes veidam savu mapes nosaukumu.
kartes_veidi = {reljefs: "reljefs", slipums: "slipums"}
#kartes_veidi = {reljefs: "reljefs", slipums: "slipums", reljefs_linijas: "reljefs_linijas", reljefs_slipums: "reljefs_slipums", reljefs_slipums_linijas: "reljefs_slipums_linijas", slipums_linijas: "slipums_linijas"}

# Izveido sesiju, lai atkārtoti izmantotu LVM GEO savienojumus. Šis ļoti paātrina fotofiksācijas darbību, jo nav jāveido jauns servera savienojums priekš katras bildes.
session = requests.Session()

# Nosaka programmas režīmu.
print(f"\n-----{Fore.CYAN} ATTĒLU UZŅEMŠANAS REŽĪMI {Fore.RESET}-----\n")
print(f"     {Fore.CYAN}1.{Fore.RESET} pilskalnu režīms\n       - Programma uzņems attēlus ar jau izvēlētiem pilskalniem.\n       - Šajā režīmā pilskalnu koordinātas ir jau definētas.\n")
print(f"     {Fore.CYAN}2.{Fore.RESET} parasto teritoriju režīms\n       - Programma uzņems attēlus ar jau izvēlētām teritorijām.\n       - Šajā režīmā teritoriju koordinātas ir jau definētas.\n")
print(f"     {Fore.CYAN}3.{Fore.RESET} specifisko teritoriju režīms\n       - Programma uzņems attēlus noteiktajā koordinātu teritorijā.\n       - Šajā režīmā jāievada teritoriju robežu koordinātas.\n       - Definējot teritoriju kā punktu, var uzņemt konkrēti vienu attēlu.\n")
print(f"     Veicot fotofiksāciju {Fore.CYAN}1.{Fore.RESET} un pēc tam {Fore.CYAN}2.{Fore.RESET} režīmā, veidojas izmantotā algoritma datu kopa.")
print(f"     Attēli {Fore.CYAN}1.{Fore.RESET} un {Fore.CYAN}2.{Fore.RESET} režīmā tiks saglabāti algoritma_datu_kopa mapē, bet {Fore.CYAN}3.{Fore.RESET} režīmā specifiska_teritorija mapē.")

while True: 
    mode = input(f"\n- Lūdzu nosakiet programmas režīmu (rakstiet {Fore.CYAN}1{Fore.RESET}, {Fore.CYAN}2{Fore.RESET} vai {Fore.CYAN}3{Fore.RESET}): {Fore.CYAN}").strip()
    
    if mode == "1":
        print(f"{Fore.RESET}- {Fore.GREEN}Foto fiksācija tiks veikta pilskalnu režīmā.{Fore.RESET}\n")
        print(f"-----{Fore.CYAN} PILSKALNU REŽĪMS {Fore.RESET}-----")
        break
    if mode == "2":
        print(f"{Fore.RESET}- {Fore.GREEN}Foto fiksācija tiks veikta parasto teritoriju režīmā.{Fore.RESET}\n")
        print(f"-----{Fore.CYAN} PARASTO TERITORIJU REŽĪMS {Fore.RESET}-----")
        break
    if mode == "3":
        print(f"{Fore.RESET}- {Fore.GREEN}Foto fiksācija tiks veikta specifisko teritoriju režīmā.{Fore.RESET}\n")
        print(f"-----{Fore.CYAN} SPECIFISKO TERITORIJU REŽĪMS {Fore.RESET}-----")
        break
    else:
        print(f"{Fore.RESET}- {Fore.RED}Nederīga izvēle! Ievadiet {Fore.CYAN}1{Fore.RED}, {Fore.CYAN}2{Fore.RED} vai {Fore.CYAN}3{Fore.RED}!{Fore.RESET}")

# Pirmā uzņemtā attēla numura ievade.
while True:
    try:
        image_id = int(input(f"\n- Ar kādu numuru tiks nosaukts pirmais uzņemtais attēls: {Fore.CYAN}"))
        
        if image_id <= 0:
            print(f"{Fore.RESET}- {Fore.RED}Vērtībai jābūt naturālam skaitlim!{Fore.RESET}")
        else:
            print(f"{Fore.RESET}- {Fore.GREEN}Paldies! Numurs derīgs.{Fore.RESET}")
            
            image_id_original = image_id    # Saglabā oriģinālo vērtību.
            
            break
    except:
        print(f"{Fore.RESET}- {Fore.RED}Vērtībai jābūt naturālam skaitlim!{Fore.RESET}")

# Veido algoritma_datu_kopa mapi, ja tā jau nepastāv.
if mode == "1" or mode == "2":
    os.makedirs("algoritma_datu_kopa", exist_ok=True)

# Pilskalnu režīms.
if mode == "1":
    # Izvēlēto pilskalnu nosaukumi ar to atrašanās koordinātām.
    # Pilskalni, kas tika izvēlēti, bet izņemti no saraksta algoritma pārbaudei:
    #   - "Gribuļu pilskalns": [56.58872, 27.36869]
    #   - "Dagdas pilskalns": [56.10536, 27.53888]
    #   - "Silaješku pilskalns": [57.15694, 26.26512]
    #   - "Bānūžu pilskalns": [57.15287, 25.57436]
    #   - "Piltiņkalns": [57.49235, 25.04525]

    # Attēlu daudzums.
    image_count_per_folder = len(pilskalni)
    image_count = image_count_per_folder * len(kartes_veidi)

    # Priekš pareizas gramatikas koda terminālī.
    if image_count_per_folder != 1:
        print(f"\n- Tiks uzņemti {Fore.CYAN}{image_count_per_folder}{Fore.RESET} attēli katrā karšu veidu mapē. Tātad kopā {Fore.CYAN}{image_count}{Fore.RESET} attēli.\n")
    elif image_count_per_folder == 1 and image_count != 1:
        print(f"\n- Tiks uzņemts {Fore.CYAN}{image_count_per_folder}{Fore.RESET} attēls katrā karšu veidu mapē. Tātad kopā {Fore.CYAN}{image_count}{Fore.RESET} attēli.\n")
    else:
        print(f"\n- Tiks uzņemts {Fore.CYAN}{image_count_per_folder}{Fore.RESET} attēls katrā karšu veidu mapē. Tātad kopā {Fore.CYAN}{image_count}{Fore.RESET} attēls.\n")
    
    # Priekš pareizas gramatikas koda terminālī.
    if image_count != 1:
        print("- Tiek sākta attēlu uzņemšana.")                                                                    
    else:
        print("- Tiek sākta attēla uzņemšana.") 

    # Pilskalnu attēlu uzņemšana.
    for kartes_veids, destination_folder in kartes_veidi.items():                                       # Veic nākamās cikla līnijas katram karšu veidam attiecīgajā mapē.
        destination_location = os.path.join("algoritma_datu_kopa", "pilskalni", destination_folder)     # Veido pilskalnu mapi.
        os.makedirs(destination_location, exist_ok=True)                                                # Veido mapi un apakšmapi attiecīgajam kartes veidam, ja tā jau nepastāv.

        for name, coords in pilskalni.items():                                                          # Veic pilskalnu attēlu uzņemšanu.
            
            # Formatē koordinātas priekš WMS URL.
            latitude, longitude = coords
            x_lks, y_lks = coordinate_transformer.transform(longitude, latitude)

            # WMS pieprasījuma URL.
            wms_url = f"https://lvmgeoserver.lvm.lv/geoserver/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=public:{kartes_veids}&STYLES=&CRS=EPSG:3059&BBOX={y_lks-image_meters/2},{x_lks-image_meters/2},{y_lks+image_meters/2},{x_lks+image_meters/2}&WIDTH={image_size}&HEIGHT={image_size}&FORMAT=image/png"

            picture = session.get(wms_url)                                  # Iegūst attēlu no URL.
            file_name = f"pilskalns_{destination_folder}_{image_id}.png"    # Nosauc failu attiecīgi izvēlētajam režīmam un numuram.

            # Veido attēla failu.
            if picture.status_code == 200:
                with open(os.path.join(destination_location, file_name), "wb") as picture_file:
                    picture_file.write(picture.content)
            
            image_id += 1               # Sagatavo numuru nākamajam attēlam.
        
        image_id = image_id_original    # Atgriež atpakaļ oriģinālo numura vērtību, lai nākamajā cikla reizē, pirmais uzņemtais attēls (atbilstošajā mapē) tiktu nosaukts ar definēto pirmo numuru.

    # Priekš pareizas gramatikas koda terminālī.
    if image_count != 1 and len(pilskalni) > 1:
        print("- Visi pilskalnu attēli tika veiksmīgi uzņemti!\n")
    elif image_count != 1 and len(pilskalni) == 1:
        print("- Pilskalnu attēli tika veiksmīgi uzņemti!\n")
    else:
        print("- Pilskalnu attēls tika veiksmīgi uzņemts!\n")

    print("--------------------------")

# Parasto teritoriju režīms.
if mode == "2":
    image_id_start_territory = image_id_original    # Ar šo mainīgo tiks saglabāts katras nākamās teritorijas pirmā attēla numurs.
    print("")

    for territory_data in defined_territory:
        territory_name, latitude_1, longitude_1, latitude_2, longitude_2 = territory_data

        if latitude_1 < latitude_2:
            print(f"{Fore.RESET}- {Fore.RED}{territory_name} teritorijas kreisā augšējā punkta platuma koordinātai jābūt lielākai vai vienādai par labā apakšējā.{Fore.RESET}\n")
            break

        if longitude_1 > longitude_2:
            print(f"{Fore.RESET}- {Fore.RED}{territory_name} teritorijas kreisā augšējā punkta garuma koordinātai jābūt mazākai vai vienādai par labā apakšējā.{Fore.RESET}\n")
            break

        # Pārveido definētos stūra punktus uz LKS-92 (EPSG:3059) sistēmas metriem.
        x1_lks, y1_lks = coordinate_transformer.transform(longitude_1, latitude_1)  # Augšējais kreisais stūris teritorijā.
        x2_lks, y2_lks = coordinate_transformer.transform(longitude_2, latitude_2)  # Apakšējais labais stūris teritorijā.

        # Saglabā šos mainīgos jaunos mainīgajos, kuri netiks mainīti. Šīs vērtības tiks pielietotas, lai izsauktu funkcijas vairākas reizes tādā pašā veidā kā iepriekšējā, jebšu, lai būtu tāds pats pirmā attēla numurs un teritorija. Šis ir vienkāršākais atrisinājums.
        x1_lks_original = x1_lks                                                      
        y1_lks_original = y1_lks                                                      

        # Atrod definētā laukuma (teritorijas) malu garumus metros.
        total_width = x2_lks - x1_lks
        total_height = y1_lks - y2_lks

        # Atrod attēlu skaitu, kas tiks uzņemts.
        # Ja grādu starpība ir 0, tad tāpat ir jāuzņem viens attēls šajā virzienā. Tā, piemēram, var uzņemt punktveida teritorijas attēlu.
        # Ja grādu starpība ir lielāka par 0, tad paredzētais attēlu skaits (konkrētajā virzienā) obligāti ir jānoapaļo uz augšu, lai būtu vesels skaits attēlu.
        if total_height > 0:
            images_in_column = math.ceil(total_height / increase)
        else:
            images_in_column = 1

        if total_width > 0:
            images_in_row = math.ceil(total_width / increase)
        else:
            images_in_row = 1
            
        image_count_per_folder = images_in_column * images_in_row
        image_count = image_count_per_folder * len(kartes_veidi)
        
        # Priekš pareizas gramatikas koda terminālī.
        if image_count_per_folder != 1:
            print(f"- Tiek sākta fotofiksācija {Fore.CYAN}{territory_name}{Fore.RESET} teritorijai. Tiks veikti {Fore.CYAN}{image_count_per_folder}{Fore.RESET} attēli katrā karšu veidu mapē. Tātad kopā {Fore.CYAN}{image_count}{Fore.RESET} attēli.")
        elif image_count_per_folder == 1 and image_count != 1:
            print(f"- Tiek sākta fotofiksācija {Fore.CYAN}{territory_name}{Fore.RESET} teritorijai. Tiks veikts {Fore.CYAN}{image_count_per_folder}{Fore.RESET} attēls katrā karšu veidu mapē. Tātad kopā {Fore.CYAN}{image_count}{Fore.RESET} attēli.")
        else:
            print(f"- Tiek sākta fotofiksācija {Fore.CYAN}{territory_name}{Fore.RESET} teritorijai. Tiks veikts {Fore.CYAN}{image_count_per_folder}{Fore.RESET} attēls katrā karšu veidu mapē. Tātad kopā {Fore.CYAN}{image_count}{Fore.RESET} attēls.")

        # Funkcija, kas uzņems parasto teritoriju attēlus no WMS servera.
        def take_region_photos(kartes_veids, destination_folder, destination_location):
            global x1_lks, y1_lks, x2_lks, y2_lks, x1_lks_original, image_id    # Izsauc jau definētos mainīgos.

            for column_images in range(images_in_column):
                for row_images in range(images_in_row):

                    # WMS pieprasījuma URL.
                    wms_url = f"https://lvmgeoserver.lvm.lv/geoserver/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=public:{kartes_veids}&STYLES=&CRS=EPSG:3059&BBOX={y1_lks-image_meters/2},{x1_lks-image_meters/2},{y1_lks+image_meters/2},{x1_lks+image_meters/2}&WIDTH={image_size}&HEIGHT={image_size}&FORMAT=image/png"

                    # Iegūst attēlu no URL.
                    picture = session.get(wms_url)

                    # Nosauc failu attiecīgi izvēlētajam režīmam.
                    file_name = f"parasta_teritorija_{destination_folder}_{image_id}.png"

                    # Veido mapi un apakšmapi attiecīgajam kartes veidam, ja tā jau neeksistē.
                    os.makedirs(destination_location, exist_ok=True)

                    # Veido attēla failu.
                    if picture.status_code == 200:
                        with open(os.path.join(destination_location, file_name), "wb") as picture_file:
                            picture_file.write(picture.content)
                    
                    # Sagatavo atbilstošos mainīgos nākamajam attēlam.
                    x1_lks = x1_lks + increase
                    image_id += 1
                
                # Sagatavo atbilstošos mainīgos nākamās kolonnas attēlam.
                x1_lks = x1_lks_original
                y1_lks = y1_lks - increase
                        
        # Pareizi izsauc funkciju, kas veiks parasto teritoriju attēlu uzņemšanu katrā kartes veidā.
        for kartes_veids, destination_folder in kartes_veidi.items():                                               # Veic nākamās cikla līnijas katram karšu veidam attiecīgajā mapē.
            image_id = image_id_start_territory                                                                     # Nodrošina, lai katrā teritorijā ir pareizais pirmā attēla numurs.

            destination_location = os.path.join("algoritma_datu_kopa", "parastas_teritorijas", destination_folder)  # Veido parasto teritoriju mapi.
            take_region_photos(kartes_veids, destination_folder, destination_location)                              # Veic parasto teritoriju attēlu uzņemšanu.
            
            # Atgriež atpakaļ oriģinālajās vērtībās, lai nākamajā cikla reizē, funkcija tiktu izpildīta tādā pašā veidā, kur ir definēts tas pats pirmā attēla numurs un teritorija.
            x1_lks = x1_lks_original
            y1_lks = y1_lks_original
        
        image_id_start_territory = image_id_start_territory + image_count_per_folder    # Nodrošina, lai nākamās teritorijas numurs ir pareizs. 

    # Attēlu skaits.
    image_count_per_folder_total = image_id_start_territory - image_id_original
    image_count_total = image_count_per_folder_total * len(kartes_veidi)

    # Priekš pareizas gramatikas koda terminālī.
    if len(defined_territory) != 1:
        print("\n- Visu parasto teritoriju attēli tika veiksmīgi uzņemti.")
    else:
        if image_count_total == 1:
            print("\n- Parastās teritorijas attēls tika veiksmīgi uzņemts.")
        else:
            print("\n- Parastās teritorijas attēli tika veiksmīgi uzņemti.")

    # Priekš pareizas gramatikas koda terminālī.
    if image_count_per_folder_total != 1:
        print(f"- Tika uzņemti {Fore.CYAN}{image_count_per_folder_total}{Fore.RESET} attēli katrā karšu veidu mapē. Tātad kopā {Fore.CYAN}{image_count_total}{Fore.RESET} attēli.\n")
    elif image_count_per_folder_total == 1 and image_count_total != 1:
        print(f"- Tika uzņemts {Fore.CYAN}{image_count_per_folder_total}{Fore.RESET} attēls katrā karšu veidu mapē. Tātad kopā {Fore.CYAN}{image_count_total}{Fore.RESET} attēli.\n")
    else:
        print(f"- Tika uzņemts {Fore.CYAN}{image_count_per_folder_total}{Fore.RESET} attēls katrā karšu veidu mapē. Tātad kopā {Fore.CYAN}{image_count_total}{Fore.RESET} attēls.\n")

    print("--------------------------")

# Specifisko teritoriju režīms. Šis kods ir līdzīgs 2. režīma kodam.
if mode == "3":

    # Teritoriju datu ievade koda terminālī.
    print(f"\n- Nosakiet teritoriju koordinātas, kur tiks uzņemti attēli.\n- Definējiet teritorijas kreisā augšējā punkta un labā apakšējā punkta ģeogrāfisko grādu koordinātas.\n")

    while True:
        try:
            latitude_1 = float(input(f"- Kreisā augšējā punkta platuma koordināta grādos (piemēram, {Fore.CYAN}57.11710{Fore.RESET}): {Fore.CYAN}"))                # 57.11710
            longitude_1 = float(input(f"{Fore.RESET}- Kreisā augšējā punkta garuma koordināta grādos (piemēram, {Fore.CYAN}26.98152{Fore.RESET}): {Fore.CYAN}"))    # 26.98152
            latitude_2 = float(input(f"{Fore.RESET}- Labā apakšējā punkta platuma koordināta grādos (piemēram, {Fore.CYAN}57.11249{Fore.RESET}): {Fore.CYAN}"))     # 57.11249
            longitude_2 = float(input(f"{Fore.RESET}- Labā apakšējā punkta garuma koordināta grādos (piemēram, {Fore.CYAN}26.99075{Fore.RESET}): {Fore.CYAN}"))     # 26.99075

            if latitude_1 < latitude_2:
                print(f"{Fore.RESET}- {Fore.RED}Kreisā augšējā punkta platuma koordinātai jābūt lielākai vai vienādai par labā apakšējā.{Fore.RESET}\n")
                continue

            if longitude_1 > longitude_2:
                print(f"{Fore.RESET}- {Fore.RED}Kreisā augšējā punkta garuma koordinātai jābūt mazākai vai vienādai par labā apakšējā.{Fore.RESET}\n")
                continue
            
            print(f"{Fore.RESET}- {Fore.GREEN}Paldies! Koordinātas derīgas.{Fore.RESET}\n")
            break

        except:
            print(f"{Fore.RESET}- {Fore.RED}Vērtībai jābūt skaitlim!{Fore.RESET}\n")
            
    # Pārveido definētos stūra punktus uz LKS-92 (EPSG:3059) sistēmas metriem.
    x1_lks, y1_lks = coordinate_transformer.transform(longitude_1, latitude_1)  # Augšējais kreisais stūris teritorijā.
    x2_lks, y2_lks = coordinate_transformer.transform(longitude_2, latitude_2)  # Apakšējais labais stūris teritorijā.

    # Saglabā šos mainīgos jaunos mainīgajos, kuri netiks mainīti. Šīs vērtības tiks pielietotas, lai izsauktu funkcijas vairākas reizes tādā pašā veidā kā iepriekšējā, jebšu, lai būtu tāds pats pirmā attēla numurs un teritorija. Šis ir vienkāršākais atrisinājums.
    x1_lks_original = x1_lks                                                      
    y1_lks_original = y1_lks                                                      

    # Atrod definētā laukuma (teritorijas) malu garumus metros.
    total_width = x2_lks - x1_lks
    total_height = y1_lks - y2_lks

    # Atrod attēlu skaitu, kas tiks uzņemts.
    # Ja grādu starpība ir 0, tad tāpat ir jāuzņem viens attēls šajā virzienā. Tā, piemēram, var uzņemt punktveida teritorijas attēlu.
    # Ja grādu starpība ir lielāka par 0, tad paredzētais attēlu skaits (konkrētajā virzienā) obligāti ir jānoapaļo uz augšu, lai būtu vesels skaits attēlu.
    if total_height > 0:
        images_in_column = math.ceil(total_height / increase)
    else:
        images_in_column = 1

    if total_width > 0:
        images_in_row = math.ceil(total_width / increase)
    else:
        images_in_row = 1
        
    image_count_per_folder = images_in_column * images_in_row
    image_count = image_count_per_folder * len(kartes_veidi)

    # Priekš pareizas gramatikas koda terminālī.
    if image_count_per_folder > 1:
        print(f"- Tiks uzņemti {Fore.CYAN}{image_count_per_folder}{Fore.RESET} attēli katrā karšu veidu mapē.\n- Tātad kopā {Fore.CYAN}{image_count}{Fore.RESET} attēli.\n")
    elif image_count_per_folder == 1 and image_count != 1:
        print(f"- Tiks uzņemts {Fore.CYAN}{image_count_per_folder}{Fore.RESET} attēls katrā karšu veidu mapē.\n- Tātad kopā {Fore.CYAN}{image_count}{Fore.RESET} attēli.\n")
    else:
        print(f"- Tiks uzņemts {Fore.CYAN}{image_count_per_folder}{Fore.RESET} attēls katrā karšu veidu mapē.\n- Tātad kopā {Fore.CYAN}{image_count}{Fore.RESET} attēls.\n")

    # Funkcija, kas uzņems specifisko teritoriju attēlus no WMS servera.
    def take_region_photos(kartes_veids, destination_folder, destination_location):
        global x1_lks, y1_lks, x2_lks, y2_lks, x1_lks_original, image_id    # Izsauc jau definētos mainīgos.

        # Pa katru rindu un kolonnu.
        for column_images in range(images_in_column):
            for row_images in range(images_in_row):

                # WMS pieprasījuma URL.
                wms_url = f"https://lvmgeoserver.lvm.lv/geoserver/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=public:{kartes_veids}&STYLES=&CRS=EPSG:3059&BBOX={y1_lks-image_meters/2},{x1_lks-image_meters/2},{y1_lks+image_meters/2},{x1_lks+image_meters/2}&WIDTH={image_size}&HEIGHT={image_size}&FORMAT=image/png"

                # Iegūst attēlu no URL.
                picture = session.get(wms_url)

                # Nosauc failu attiecīgi izvēlētajam režīmam.
                file_name = f"specifiska_teritorija_{destination_folder}_{image_id}.png"

                # Veido mapi un apakšmapi attiecīgajam kartes veidam, ja tā jau neeksistē.
                os.makedirs(destination_location, exist_ok=True)

                # Veido attēla failu.
                if picture.status_code == 200:
                    with open(os.path.join(destination_location, file_name), "wb") as picture_file:
                        picture_file.write(picture.content)
                
                # Sagatavo atbilstošos mainīgos nākamajam attēlam.
                x1_lks = x1_lks + increase
                image_id += 1
            
            # Sagatavo atbilstošos mainīgos nākamās kolonnas attēlam.
            x1_lks = x1_lks_original
            y1_lks = y1_lks - increase

    # Priekš pareizas gramatikas koda terminālī.
    if image_count > 1:
        print("- Tiek sākta attēlu uzņemšana.")                             
    else:
        print("- Tiek sākta attēla uzņemšana.")     

    # Pareizi izsauc funkciju, kas veiks specifisko teritoriju attēlu uzņemšanu katrā kartes veidā.
    for kartes_veids, destination_folder in kartes_veidi.items():                                   # Veic nākamās cikla līnijas katram karšu veidam attiecīgajā mapē.
        destination_location = os.path.join("specifiska_teritorija", destination_folder)            # Veido specifisko teritoriju mapi.
        take_region_photos(kartes_veids, destination_folder, destination_location)                  # Veic specifisko teritoriju attēlu uzņemšanu.
        
        # Atgriež atpakaļ oriģinālajās vērtībās, lai nākamajā cikla reizē, funkcija tiktu izpildīta tādā pašā veidā, kur ir definēts tas pats pirmā attēla numurs un teritorija.
        image_id = image_id_original
        x1_lks = x1_lks_original
        y1_lks = y1_lks_original

    # Priekš pareizas gramatikas koda terminālī.
    if image_count > 1:
        print("- Visi specifiskās teritorijas attēli tika veiksmīgi uzņemti.\n")
    else:
        print("- Specifiskās teritorijas attēls tika veiksmīgi uzņemts.\n")
    
    print("--------------------------")