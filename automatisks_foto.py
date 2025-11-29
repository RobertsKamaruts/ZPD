from pyproj import Transformer          # Pārveidos koordinātas no vienas koordinātu sistēmas uz citu.
from colorama import Fore               # Formatēs tekstu terminālī.
import requests                         # Iegūs bildes no WMS servera.
import math                             # Atļaujs apaļot skaitļus.
import os                               # Darobosies ar mapēm.

# Pamatu iestatījumi.
coordinate_transformer = Transformer.from_crs("EPSG:4326", "EPSG:3059", always_xy=True)     # Pārveidos koordinātas uz LKS-92 metru sistēmas.
image_size = 512                                                                            # Ekrānuzņēmuma platums un augstums pikseļos, kur 1 pikselis atbilst 1 metram.

# Kartes veidi WMS pieprasījuma URL. Šeit ir pieejami dažādi kartes veidi, bet programma lietos tikai divus, lai ietaupītu resursus.
reljefs = "ZemeLKS"
slipums_linijas = "Slope_contours"
#reljefs_linijas = "DTM_contours"
#reljefs_slipums = "SlopeDTM"
#reljefs_slipums_linijas = "SlopeDTM_contours"
#slipums = "SlopeLKS"

# Piefiksē katram kartes veidam savu mapes nosaukumu. Programma lietos tikai divus kartes veidus, tāpēc nav vajadzībā definēt tos, kurus nelietos.
kartes_veidi = {reljefs: "reljefs", slipums_linijas: "slipums_linijas"}
#kartes_veidi = {reljefs: "reljefs", reljefs_linijas: "reljefs_linijas", reljefs_slipums: "reljefs_slipums", reljefs_slipums_linijas: "reljefs_slipums_linijas", slipums: "slipums", slipums_linijas: "slipums_linijas"}

# Nosaka programmas režīmu.
print(f"\n-----{Fore.CYAN} BILŽU UZŅEMŠANAS REŽĪMI {Fore.RESET}-----\n")
print(f"     1. pilskalnu režīms\n       - Programma automātiski uzņems bildes ar specifiskiem pilskalniem.\n       - Šajā režīmā pilskalnu koordinātas ir jau definētas.\n")
print(f"     2. reģionu režīms\n       - Programma automātiski uzņems bildes noteiktajā koordinātu reģionā.\n       - Šajā režīmā jāievada reģionu robežu koordinātas.\n")

while True: 
    mode = input(f"\n- Lūdzu nosakiet programmas režīmu (rakstiet {Fore.CYAN}1{Fore.RESET} priekš pilskalnu vai {Fore.CYAN}2{Fore.RESET} priekš reģionu): {Fore.CYAN}").strip()
    
    if mode == "1":
        print(f"{Fore.RESET}- {Fore.GREEN}Pilskalnu režīms izvēlēts!{Fore.RESET}\n")
        print(f"-----{Fore.CYAN} PILSKALNU REŽĪMS {Fore.RESET}-----")
        break
    if mode == "2":
        print(f"{Fore.RESET}- {Fore.GREEN}Reģionu režīms izvēlēts!{Fore.RESET}\n")
        print(f"-----{Fore.CYAN} REĢIONU REŽĪMS {Fore.RESET}-----")
        break
    else:
        print(f"{Fore.RESET}- {Fore.RED}Nederīga izvēle! Ievadiet {Fore.CYAN}1{Fore.RED} vai {Fore.CYAN}2{Fore.RESET}.")

# Reģionu režīms.
if mode == "2":

    # Reģionu datu ievade koda terminālī.
    print(f"\n- Nosakiet reģiona koordinātas, kur tiks uzņemtas bildes.\n- Definējiet reģiona kreisā augšējā punkta un labā apakšējā punkta ģeogrāfisko grādu koordinātas.\n")

    while True:
        try:
            latitude_1 = float(input(f"- Kreisā augšējā punkta platuma koordināta grādos (piemēram, {Fore.CYAN}57.11710{Fore.RESET}): {Fore.CYAN}"))     # 57.11710
            longitude_1 = float(input(f"{Fore.RESET}- Kreisā augšējā punkta garuma koordināta grādos (piemēram, {Fore.CYAN}26.98152{Fore.RESET}): {Fore.CYAN}"))     # 26.98152
            latitude_2 = float(input(f"{Fore.RESET}- Labā apakšējā punkta platuma koordināta grādos (piemēram, {Fore.CYAN}57.11249{Fore.RESET}): {Fore.CYAN}"))      # 57.11249
            longitude_2 = float(input(f"{Fore.RESET}- Labā apakšējā punkta garuma koordināta grādos (piemēram, {Fore.CYAN}26.99075{Fore.RESET}): {Fore.CYAN}"))      # 26.99075

            if latitude_1 < latitude_2:
                print(f"{Fore.RESET}- {Fore.RED}Kreisā augšējā punkta platuma koordinātei jabūt lielākai (vai vienādai) nekā labā apakšējā.{Fore.RESET}\n")
                continue

            if longitude_1 > longitude_2:
                print(f"{Fore.RESET}- {Fore.RED}Kreisā augšējā punkta garuma koordinātei jabūt mazākai (vai vienādai) nekā labā apakšējā.{Fore.RESET}\n")
                continue
            
            print(f"{Fore.RESET}- {Fore.GREEN}Paldies! Koordinātas ir derīgas.{Fore.RESET}\n")
            break

        except:
            print(f"{Fore.RESET}- {Fore.RED}Vērtībai jābūt skaitlim!{Fore.RESET}\n")

    while True:
        try:
            image_id = int(input(f"- Ar kādu numuru tiks nosaukta pirmā uzņemtā bilde (piemēram, {Fore.CYAN}parasta_teritorija_5.png{Fore.RESET} -> {Fore.CYAN}5{Fore.RESET}): {Fore.CYAN}"))
            
            if image_id <= 0:
                print(f"{Fore.RESET}- {Fore.RED}Vērtībai jābūt naturālam skaitlim!{Fore.RESET}\n")
            else:
                print(f"{Fore.RESET}- {Fore.GREEN}Paldies! Numurs ir derīgs.{Fore.RESET}\n")
                break
        except:
            print(f"{Fore.RESET}- {Fore.RED}Vērtībai jābūt naturālam skaitlim!{Fore.RESET}\n")
            
    increase = 51.2                                                                 # Par tik lielu metru attālumu tiks uzņemta nākamā bilde virziena virknē.

    # Pārveido definētos stūra punktus uz LKS-92 (EPSG:3059) sistēmas metriem.
    x1_lks, y1_lks = coordinate_transformer.transform(longitude_1, latitude_1)      # Augšējais kreisais stūris reģionā.
    x2_lks, y2_lks = coordinate_transformer.transform(longitude_2, latitude_2)      # Apakšējais labais stūris reģionā.

    # Saglabā šos mainīgos jaunos mainīgajos, kuri netiks kodā mainīti. Šīs vērtības tiks pielietotas, lai izsauktu funkcijas vairākas reizes tādā pašā veidā kā iepriekšējo, jebšu, lai būtu tāds pats pirmās bildes numurs un reģions. Šis ir vienkāršākais atrisinājums.
    x1_lks_original = x1_lks                                                      
    y1_lks_original = y1_lks
    image_id_original = image_id                                                 

    # Atrod definētā laukuma (reģiona) malu garumus metros.
    total_width = x2_lks - x1_lks
    total_height = y1_lks - y2_lks

    # Atrod bilžu daudzumu, kas tiks uzņemtas.
    # Ja grādu starpība ir 0, tad tāpat ir jāuzņem viena bilde šajā virzienā. Tā, piemēram, var uzņemt punktveida reģionu.
    # Ja grādu starpība ir lielāka par 0, tad paredzētais bilžu skaits (konkrētajā virziena) obligāti ir jānoapaļo uz augšu, lai būtu vesels bilžu skaits.
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

    print(f"- Kopā tiks uzņemtas {Fore.CYAN}{image_count_per_folder}{Fore.RESET} bildes katrā mapē.\n- Tātad kopā - {Fore.CYAN}{image_count}{Fore.RESET} bildes.\n")     # Paskaidro koda terminālī, cik bildes tiks uzņemtas.

    # Funkcija, kas uzņems parasto teritoriju bildes no WMS servera.
    def take_region_photos(kartes_veids, destination_folder, destination_location):
        global x1_lks, y1_lks, x2_lks, y2_lks, x1_lks_original, image_id       # Izsauc jau definētos mainīgos.

        # Pa katru rindu un kolonnu.
        for column_images in range(images_in_column):
            for row_images in range(images_in_row):

                # WMS pieprasījuma URL.
                wms_url = f"https://lvmgeoserver.lvm.lv/geoserver/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=public:{kartes_veids}&STYLES=&CRS=EPSG:3059&BBOX={y1_lks-image_size/2},{x1_lks-image_size/2},{y1_lks+image_size/2},{x1_lks+image_size/2}&WIDTH={image_size}&HEIGHT={image_size}&FORMAT=image/png"

                # Iegūst bildi no URL.
                picture = requests.get(wms_url)

                # Nosauc failu attiecīgi izvēlētajam režīmam.
                file_name = f"parasta_teritorija_{destination_folder}_{image_id}.png"

                # Veido mapi un apakšmapi attiecīgajam kartes veidam, ja tā jau neeksitē.
                os.makedirs(destination_location, exist_ok=True)

                # Veido bildes failu.
                if picture.status_code == 200:
                    with open(os.path.join(destination_location, file_name), "wb") as picture_file:
                        picture_file.write(picture.content)
                
                # Sagatavo atbilstošos mainīgos nākamajai bildei.
                x1_lks = x1_lks + increase
                image_id += 1
            
            # Sagatavo atbilstošos mainīgos nākamajai bildei.
            x1_lks = x1_lks_original
            y1_lks = y1_lks - increase

    # Pareizi izsauc funkciju, kas uzņems parasto teritoriju bilžu uzņemšanu katrā kartes veidā.
    for kartes_veids, destination_folder in kartes_veidi.items():                           # Veic nākošās cikla līnijas priekš katra karšu veida tajā attiecīgajā mapē.
        destination_location = os.path.join("parastas_teritorijas", destination_folder)     # Veido parasto teritoriju mapi.
        take_region_photos(kartes_veids, destination_folder, destination_location)          # Veic parasto teritoriju bilžu uzņemšanu.
        
        # Atgriež atpakaļ orģinālajās vērtībās, lai nākamajā cikla reizē, funckija tiktu izpildīta tādā pašā veidā, kur ir definēts tas pats pirmais bildes numurs un reģions.
        image_id = image_id_original
        x1_lks = x1_lks_original
        y1_lks = y1_lks_original