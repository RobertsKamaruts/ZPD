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
# This programme is made as a part of the scientific paper to automate Latvian relief and slope models image capturing. It allows 
# to generate the dataset on which the paper's algorithm was trained.
# 
# The programme's different mode code sections are similar to each other, but in each one there are different and specific nuances 
# to their logic. That's why the shared parts aren't combined in a single function. In this case, this is just the technically 
# simplest and the most understandable solution.
#
# Programme created by: Roberts Kamarūts
#
# -------------------------------------------------------------------------------------------------------------------------------------

from pyproj import Transformer          # Pārveidos koordinātas no vienas koordinātu sistēmas uz citu.
from colorama import Fore               # Formatēs tekstu terminālī.
import requests                         # Iegūs attēlus no WMS servera.
import math                             # Atļaus apaļot skaitļus.
import os                               # Darbosies ar mapēm.

# Pamatu iestatījumi.
coordinate_transformer = Transformer.from_crs("EPSG:4326", "EPSG:3059", always_xy=True)     # Pārveidos koordinātas uz LKS-92 metru sistēmu.
image_size = 1024                                                                           # Attēlu platums un garums pikseļos.
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
    pilskalni = {
        "Barauhas pilskalns": [56.31944, 27.30583], "Vacslobodas": [56.34263, 27.57849], "Smaganu pilskalns": [56.29535, 27.33050], "Cērtenes pilskalns": [57.41027, 25.90032],
        "Ladušu pilskalns": [56.36972, 27.37672], "Višu pilskalns": [56.38198, 27.56948], "Bondaru pilskalns": [56.29186, 27.33856], "Zeļenopoles Krātavu kalns": [56.26869, 27.49813],
        "Viraudas pilskalns": [56.24556, 27.40065], "Pušas pilskalni": [56.23960, 27.23403], "Svātovas pilskalns": [56.22021, 27.15559], "Leimanišķu Baterijas kalns": [56.31438, 27.21843],
        "Leimanišķu pilskalns": [56.31476, 27.22451], "Gušču pilskalns": [56.37484, 27.15020], "Ķīšu kalns": [56.54085, 27.77239], "Degteru pilskalns": [56.56290, 27.87410],
        "Solomenku pilskalns": [56.38204, 27.70453], "Porkaļu pilskalns": [56.37415, 27.75173], "Divkšu pilskalns": [56.38129, 27.87022], "Pentjušu pilskalns": [56.32437, 27.88384],
        "Rudavas kalns": [56.33248, 27.91851], "Naumku pilskalns": [56.33997, 28.12059], "Zagorsku pilskalns": [56.29249, 28.04941], "Garaņu pilskalns": [56.23155, 28.16606],
        "Andžānu pilskalns": [56.11359, 27.92306], "Svātiunes pilskalns": [56.88670, 27.56151], "Dzirkaļu (Gorku) pilskalns": [56.27175, 27.64220], "Ūdrāju pilskalns": [56.21252, 27.62201],
        "Puncuļevas pilskalns": [56.90325, 27.60679], "Rubenaucu pilskalns": [56.05223, 27.67339], "Jukumu Grumuškas kalns - pilskalns I": [56.18240, 27.53392], "Jukumu Grumuškas kalns - pilskalns II": [56.18353, 27.52740],
        "Dauguļu Kapču kalns": [56.18132, 27.49384], "Stalidzānu Svilušais kalns": [56.18866, 27.37164], "Černoručjes pilskalns": [56.18058, 27.33139], "Beitānu pilskalns": [56.17134, 27.32554],
        "Slabadas Augstais kalns": [56.10576, 27.47470], "Ļutovcu Augstais kalns - pilskalns I": [56.04098, 27.55835], "Robežnieku (Pustiņas) pilskalns": [55.96857, 27.61290], "Okras pilskalns": [56.13472, 27.25787],
        "Vonogu (Vaišļu, Aulejas) pilskalns": [56.04655, 27.26692], "Ļaksu pilskalns": [55.94811, 27.47096], "Udinavas pilskalns": [55.83268, 27.48290], "Lielindricas pilskalns": [55.85779, 27.30245],
        "Daudzīšu Kazas kalns": [55.87205, 27.33980], "Borovkas pilskalns": [55.89895, 27.26473], "Krāslavas pilskalns": [55.90859, 27.16630], "Kaplavas pilskalns": [55.84951, 26.98472],
        "Vecračinas pilskalns": [55.91548, 26.93304], "Stanovišku pilskalns": [56.11750, 27.18209], "Brīveru pilskalns": [56.04452, 27.02745], "Gorodokas pilskalns": [56.11596, 27.09642],
        "Rivarišku pilskalns": [56.11095, 27.08266], "Madalānu pilskalns": [56.12015, 27.04734], "Valaiņu pilskalns": [56.08275, 27.04052], "Dudaru pilskalns": [56.19636, 27.06227],
        "Rušenicas pilskalns": [56.21590, 27.03197], "Grohoļsku pilskalns": [56.24688, 27.01743], "Kategrades pilskalns": [56.23805, 26.92961], "Silavišku pilskalns": [56.09703, 26.85610],
        "Križovkas pilskalns": [56.04291, 26.96518], "Leperu pilskalns": [56.03653, 26.92812], "Zabornajas pilskalns": [56.08552, 26.81056], "Baraukas pilskalns": [56.10677, 26.75487],
        "Liumonu pilskalns": [56.11472, 26.75444], "Kalvānu pilskalns": [56.18103, 26.71688], "Rumpu pilskalns": [56.32913, 26.67485], "Pleskavas pilskalns": [56.62228, 26.95735],
        "Mistra kalns": [57.02755, 27.58942], "Kauguru kalns": [57.24896, 27.46602], "Tempļa kalns": [57.43224, 27.05780], "Jaunķempju pilskalns": [57.24893, 26.84475],
        "Lazdu kalns": [57.19766, 26.69814], "Krapas pilskalns": [57.13232, 26.64159], "Liedes kalni": [57.05369, 26.54879], "Obzerkalns": [57.03985, 26.50912],
        "Atašienes pilskalns": [56.50874, 26.42213], "Ģedušu pilskalns": [56.44796, 26.27879], "Dzenes kalns": [56.20942, 26.26772], "Greizo kalnu pilskalns": [56.09954, 26.27725],
        "Veipieša pilskalns": [56.00199, 26.56697], "Sīķeles pilskalns": [55.87772, 26.77920], "Lasiņu pilskalns": [55.85403, 26.59758], "Kaķīšu pilskalns": [55.89601, 26.38620],
        "Ļūbasta pilskalns": [55.94253, 26.45278], "Sudmaļu pilskalns": [55.90071, 26.34321], "Lapsu kalns": [55.97043, 26.18967], "Driģeņu pilskalns": [56.00812, 26.22034],
        "Sidrabiņu pilskalns": [56.01610, 26.21296], "Palazdiņu pilskalns": [56.02053, 26.29350], "Zamečkas pilskalns": [56.03046, 26.29157], "Rūrānu Batarejas pilskalns": [56.02479, 26.20783],
        "Liepkalnu pilskalns": [56.03531, 26.19574], "Kaldabruņas pilskalns": [56.09121, 26.08101], "Radžupes pilskalns": [56.17322, 25.77420], "Aknīstes pilskalns": [56.16774, 25.73872],
        "Stupeļu kalns": [56.16952, 25.46556], "Kņāvu pilskalns": [56.22555, 25.53137], "Skosu pilskalns": [56.26153, 25.36879], "Kūliņu pilskalns": [56.32104, 25.52081],
        "Sērpiņu pilskalns": [56.41007, 25.52625], "Kaupres pilskalns": [56.47879, 25.92286], "Asotes pilskalns": [56.49295, 25.91890], "Dzirkaļu pilskalns": [56.52447, 26.03437],
        "Piksteres Zilais kalns": [56.47737, 25.55115], "Grūbeles pilskalns": [56.51164, 25.52261], "Sāvienas pilskalns": [56.66524, 26.19203], "Lazdonas pilskalns": [56.81722, 26.16727],
        "Dreimaņu pilskalns": [56.76936, 26.13974], "Sauleskalna pilskalns": [56.80367, 26.07326], "Uriekstes pilskalns": [57.20338, 26.32653], "Cauņu pilskalns": [57.43072, 26.19145],
        "Kaudžu pilskalns": [57.22119, 26.11936], "Dārznīcas kalns": [56.89294, 26.04358], "Kapusila pilskalns": [57.32755, 25.95721], "Pīkaņu Skansts kalns": [57.28350, 25.75021],
        "Ķētu pilskalns": [57.21370, 25.71922], "Dzērbenes Augstais kalns": [57.19316, 25.67945], "Vējavas pilskalns": [56.92240, 25.89259], "Aderkašu pilskalns": [56.84606, 25.35266],
        "Pekas kalns": [57.47879, 25.39047], "Sāruma kalns": [57.28655, 25.37127], "Līču pilskalns": [57.20223, 25.32254], "Riekstu kalns": [57.31373, 25.26886],
        "Vaidavas pilskalns": [57.45811, 25.26905], "Skaņkalnes pilskalns": [57.85956, 25.03238], "Vīkšēnu pilskalns": [57.84875, 25.00507], "Liepupes pilskalns": [57.46825, 24.42740],
        "Lojas pilskalns": [57.14603, 24.68296], "Grebu Bļodas kalns": [57.62101, 24.99411], "Grebu pilskalns": [57.62046, 24.99594], "Panūtes kalns": [57.35021, 24.92158],
        "Batarejas kalns Mazstraupē": [57.35931, 24.95947], "Ērgļu kalni": [57.37767, 24.96160], "Ureles pilskalns": [57.35394, 25.07307], "Kvēpenes pilskalns": [57.27685, 25.18396],
        "Vikmestes pilskalns": [57.17578, 24.82883], "Krusta kalna pilskalns": [57.16775, 24.84835], "Mālpils pilskalns": [57.00920, 24.94803], "Ķoderu pilskalns": [56.90753, 24.77068],
        "Mežotnes Vīna kalns": [56.43532, 24.04297], "Mežotnes pilskalns": [56.44149, 24.04530], "Sakaiņu pilskalns": [56.80015, 24.37529], "Daugmales pilskalns": [56.83109, 24.38250],
        "Tukuma pilskalns": [56.96853, 23.12958], "Tērvetes Svētkalns": [56.48475, 23.38293], "Incēnu pilskalns": [56.49996, 22.74298], "Spārnu pilskalns": [56.55046, 23.04290],
        "Jaunpils Kartavu kalns": [56.71702, 23.01670], "Vecmoku pilskalns": [56.99517, 23.06669], "Pūres pilskalns": [57.03709, 22.93982], "Kandavas pilskalns": [57.04105, 22.78256],
        "Buses pilskalns": [56.99151, 22.60373], "Sabiles pilskalns": [57.04684, 22.57666], "Dzegužu pilskalns": [57.14022, 22.76354], "Lībagu Kāravkalns": [57.20653, 22.60724],
        "Laucienes Milzu kalns": [57.23833, 22.64155], "Talsu pilskalns": [57.24266, 22.59917], "Puiškalna pilskalns": [57.54264, 22.51361], "Ugāles pilskalns": [57.28210, 22.03670],
        "Diždāmes un Aizvīķu pilskalni": [56.33664, 21.71100], "Kazdangas pilskalns": [56.70891, 21.74040], "Ievādes Kapličas kalns": [56.68909, 21.53423], "Vārtājas pilskalns": [56.48831, 21.38163],
        "Kundu (Turlavas) pilskalns": [56.82172, 21.87871], "Mazsāliju pilskalns": [56.87949, 21.92648], "Lipaiķu pilskalns": [56.84774, 21.77821], "Alšvangas Dižgabalkalns": [56.98091, 21.56932],
        "Padures pilskalns": [57.04312, 21.92367], "Paventu pilskalns": [57.10043, 21.83887]
    }

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
    for kartes_veids, destination_folder in kartes_veidi.items():                                                               # Veic nākamās cikla līnijas katram karšu veidam attiecīgajā mapē.
        destination_location = os.path.join("algoritma_datu_kopa", "pilskalni", destination_folder)                                # Veido pilskalnu mapi.
        os.makedirs(destination_location, exist_ok=True)                                                                   # Veido mapi un apakšmapi attiecīgajam kartes veidam, ja tā jau nepastāv.

        for name, coords in pilskalni.items():                                                                                         # Veic pilskalnu attēlu uzņemšanu.
            
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
            
            image_id += 1                                                                                   # Sagatavo numuru nākamajam attēlam.
        
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
    defined_territory = [
        ["1.", 57.29760, 25.77101, 57.27361, 25.91211],
        ["2.", 57.30668, 26.00155, 57.29871, 26.06772],
        ["3.", 57.23783, 26.07987, 57.21842, 26.11493],
        ["4.", 57.13857, 26.68330, 57.11765, 26.71188],
        ["5.", 57.10516, 26.93899, 57.06743, 26.99015],
        ["6.", 57.58237, 26.87994, 57.53762, 26.98963],
        ["7.", 57.54696, 27.20573, 57.51527, 27.26480],
        ["8.", 56.85733, 23.61151, 56.83789, 23.63640],
        ["9.", 56.42729, 21.15263, 56.42444, 21.22825],
        ["10.", 57.49530, 24.95124, 57.45312, 24.99673],
        ["11.", 57.48197, 24.99700, 57.43777, 25.12806],
        ["12.", 56.53874, 25.39340, 56.52002, 25.43594],
        ["13.", 56.72646, 25.70457, 56.69489, 25.82285],
        ["14.", 56.55582, 21.60084, 56.54943, 21.64051],
        ["15.", 56.35836, 21.71618, 56.34264, 21.76932],
        ["16.", 56.57562, 23.05713, 56.56705, 23.09588],
        ["17.", 56.27271, 28.00421, 56.25206, 28.03780],
        ["18.", 56.20647, 27.20648, 56.18225, 27.24296],
        ["19.", 57.24358, 24.87682, 57.22251, 24.97534],
        ["20.", 56.88144, 25.93082, 56.86103, 26.00747],
    ]

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
        x1_lks, y1_lks = coordinate_transformer.transform(longitude_1, latitude_1)      # Augšējais kreisais stūris teritorijā.
        x2_lks, y2_lks = coordinate_transformer.transform(longitude_2, latitude_2)      # Apakšējais labais stūris teritorijā.

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
            global x1_lks, y1_lks, x2_lks, y2_lks, x1_lks_original, image_id        # Izsauc jau definētos mainīgos.

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
        for kartes_veids, destination_folder in kartes_veidi.items():                                                   # Veic nākamās cikla līnijas katram karšu veidam attiecīgajā mapē.
            image_id = image_id_start_territory                                                                 # Nodrošina, lai katrā teritorijā ir pareizais pirmā attēla numurs.

            destination_location = os.path.join("algoritma_datu_kopa", "parastas_teritorijas", destination_folder)       # Veido parasto teritoriju mapi.
            take_region_photos(kartes_veids, destination_folder, destination_location)                                  # Veic parasto teritoriju attēlu uzņemšanu.
            
            # Atgriež atpakaļ oriģinālajās vērtībās, lai nākamajā cikla reizē, funkcija tiktu izpildīta tādā pašā veidā, kur ir definēts tas pats pirmā attēla numurs un teritorija.
            x1_lks = x1_lks_original
            y1_lks = y1_lks_original
        
        image_id_start_territory = image_id_start_territory + image_count_per_folder            # Nodrošina, lai nākamās teritorijas numurs ir pareizs. 

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
            latitude_1 = float(input(f"- Kreisā augšējā punkta platuma koordināta grādos (piemēram, {Fore.CYAN}57.11710{Fore.RESET}): {Fore.CYAN}"))                  # 57.11710
            longitude_1 = float(input(f"{Fore.RESET}- Kreisā augšējā punkta garuma koordināta grādos (piemēram, {Fore.CYAN}26.98152{Fore.RESET}): {Fore.CYAN}"))       # 26.98152
            latitude_2 = float(input(f"{Fore.RESET}- Labā apakšējā punkta platuma koordināta grādos (piemēram, {Fore.CYAN}57.11249{Fore.RESET}): {Fore.CYAN}"))        # 57.11249
            longitude_2 = float(input(f"{Fore.RESET}- Labā apakšējā punkta garuma koordināta grādos (piemēram, {Fore.CYAN}26.99075{Fore.RESET}): {Fore.CYAN}"))        # 26.99075

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
    x1_lks, y1_lks = coordinate_transformer.transform(longitude_1, latitude_1)      # Augšējais kreisais stūris teritorijā.
    x2_lks, y2_lks = coordinate_transformer.transform(longitude_2, latitude_2)      # Apakšējais labais stūris teritorijā.

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
        global x1_lks, y1_lks, x2_lks, y2_lks, x1_lks_original, image_id        # Izsauc jau definētos mainīgos.

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
    for kartes_veids, destination_folder in kartes_veidi.items():                                                   # Veic nākamās cikla līnijas katram karšu veidam attiecīgajā mapē.
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