from PIL import ImageGrab           # Veiks ekrānuzņēmumus.
import tkinter as tk                # Uzzīmēs ekrānuzņēmuma rāmi uz ekrāna.
import keyboard                     # Iegūs klaviatūras inputu.
import win32gui, win32con           # Ļauj veidot pilnīgi nekustīgus, caurspīdīgus programmas logus.
import os                           # Veiks darbības ar mapēm.

# Attiecīgā ekrāna px dimensijas. Šis ir vajadzīgi, lai atrastu ekrāna centru.
screen_width = 1920
screen_height = 1200

# Cik liels būs ekrānuzņēmuma garums un platums px.
square_size = 512 

# Atrod, kur jāuzņem ekrānuzņēmumus, lai bilde būtu ekrāna centrā.
screenshot_x = (screen_width - square_size) // 2
screenshot_y = (screen_height - square_size) // 2
screenshot_coordinates = (screenshot_x, screenshot_y, screenshot_x + square_size, screenshot_y + square_size)

# Atrod ekrāna centra koordinātas.
centre_x = screen_width // 2
centre_y = screen_height // 2

border_on = False                       # Norādīs, vai ekrānuzņēmuma rāmi vajag attēlot uz ekrāna.
screenshot_button = "["                 # Definē ar kuru pogu uz klaviatūras tiks veikts ekrānuzņēmums.
border_button = "]"                     # Definē ar kuru pogu uz klaviatūras var atvērt vai aizvērt ekrānuzņēmuma rāmi.

# Palīdzēs piešķirt katrai bildei savu numuru faila nosaukumā atbilstoši pēc aktīvā režīma.
image_id_number_1 = 1
image_id_number_2 = 1
image_id_number_3 = 1
image_id_number_4 = 1

# Definē ar kurām pogām uz klaviatūras var mainīt ekrānuzņēmuma bildes saglabāšanas vietu.
first_mode_button = "1"
second_mode_button = "2"
third_mode_button = "3"
fourth_mode_button = "4"

# Paskaidro programmas nosacījumus koda terminālī.
print(f'\nLai veiktu ekrānuzņēmumu, nospiediet "{screenshot_button}" pogu.')
print(f'Lai atvērtu vai aizvērtu ekrānuzņēmuma rāmi, nospiediet "{border_button}" pogu.')
print("Lai mainītu režīmu, kurā mapē tiks saglabāts ekrānuzņēmums nospiediet:\n")
print(fr'    "{first_mode_button}" priekš ...\ZPD\reljefa_modelis\pilskalnu_teritorijas')
print(fr'    "{second_mode_button}" priekš ...\ZPD\augstumliknu_reljefa_slipuma_modelis\pilskalnu_teritorijas')
print(fr'    "{third_mode_button}" priekš ...\ZPD\reljefa_slipuma_modelis\pilskalnu_teritorijas')
print(fr'    "{fourth_mode_button}" priekš ...\ZPD{"\n"}')

# Šajās mapēs tiks ierakstīti ekrānuzņēmumi.
folders = ["reljefa_modelis", "augstumliknu_reljefa_slipuma_modelis", "reljefa_slipuma_modelis"]
subfolders = ["pilskalnu_teritorijas", "parastas_teritorijas"]

# Veido šajā mapē 3 jaunas mapes, kur katrā iekšā veido 2 jaunas apakšmapes, ja tās jau neeksistē.
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)
    for subfolder in subfolders:
        subfolder_path = os.path.join(folder, subfolder)
        
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)

# Definē logu, "zīmēšanas virsmu" un rāmi. 
# Šis ir vajadzīgs, lai tiem jau būtu kāda sākotnējā vērtība neatkarīgi no lietotāja darbību secības.
overlay = None
canvas = None
border = None
horizontal_line = None
vertical_line = None

# Funkcijas, kas uzzīmē rāmi uz ekrāna.
def draw_border():
    global border_on, overlay, canvas, border, horizontal_line, vertical_line   # Izsauc jau definētos mainīgos.

    if overlay == None:                                                         # Šis nosacījums ir vajadzīgs, lai veidotu logu un zīmešanas virsmu tikai pirmaja reizē, kad šī funkcija tiek izsaukta.
        overlay = tk.Tk()                                                       # Izveido jaunu logu.

        # Logu padara caurspīdīgu. Šeit tiek definēta krāsa, kas visā logā būs caurspīdīga. 
        # Tas ir viens no Tkinter ierobežojumiem, jo precīzi šajā krāsā nevarēs uzzīmēt rāmi vai citus objektus. Tie tad būtu caurspīdīgi.
        transparent_colour = "#123456"
        overlay.config(bg=transparent_colour)
        overlay.attributes("-transparentcolor", transparent_colour)         

        # Logu arī padara vienmēr redzamu, netiešu un definē loga platumu, augstumu un pozīciju.
        overlay.attributes("-topmost", True)                        
        overlay.overrideredirect(True)
        overlay.geometry(f"{screen_width}x{screen_height}+0+0")      # "+0+0" precizē, ka logs jāzīmē ekrāna (0, 0) koordinātās.

        # Definē un attēlo zīmēšanas virsmu, kura ir caurspīdīga, un uz kuras tiks uzzīmēts ekrānuzņēmuma rāmis.
        canvas = tk.Canvas(overlay, width=screen_width, height=screen_height, bg=transparent_colour, highlightthickness=0)
        canvas.pack()

        # Uzzīmē rāmi.
        horizontal_line = canvas.create_line(screenshot_x, centre_y, screenshot_x + square_size, centre_y, fill="#ffffff", width=1)
        vertical_line = canvas.create_line(centre_x, screenshot_y, centre_x, screenshot_y + square_size, fill="#ffffff", width=1)
        border = canvas.create_rectangle(screenshot_x, screenshot_y, screenshot_x + square_size, screenshot_y + square_size, outline="#ffffff", width=4)

        # Attēlo logu un norāda, ka ekrānuzņemuma rāmis ir uzzīmēts.
        overlay.update()                            
        border_on = True

        # Padara logu pilnīgi caurspiežamu. Tkinter pats par sevi nevar izveidot pilnīgi caurspiežamu logu. Pat caurspīdīgs logs var reģistrēt klikšķus.
        # win32gui ļauj izmantot Windows API, lai logs būtu tikai vizuāls.
        handle_to_window = int(overlay.frame(), 16)                                                                                     # Iegūst loga "handle" jeb identifikatoru pareizā formatā.
        styles = win32gui.GetWindowLong(handle_to_window, win32con.GWL_EXSTYLE)                                                         # Nolasa loga stila iestatījumus.
        win32gui.SetWindowLong(handle_to_window, win32con.GWL_EXSTYLE, styles | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED)    # Papildina loga stila iestatījumus.
        
        return border_on, overlay, canvas, border, horizontal_line, vertical_line                                                       # Atgriež mainīgos.
    else:
        # Ja logs jau ir izveidots, nevajag definēt vēl vienu logu un zīmēšanas virsmu, bet gan tikai jaunu rāmi.

        # Uzzīmē rāmi.
        horizontal_line = canvas.create_line(screenshot_x, centre_y, screenshot_x + square_size, centre_y, fill="#ffffff", width=1)
        vertical_line = canvas.create_line(centre_x, screenshot_y, centre_x, screenshot_y + square_size, fill="#ffffff", width=1)
        border = canvas.create_rectangle(screenshot_x, screenshot_y, screenshot_x + square_size, screenshot_y + square_size, outline="#ffffff", width=4)
        
        # Atjauno logu un norāda, ka ekrānuzņemuma rāmis ir uzzīmēts.
        overlay.update()                            
        border_on = True

        return border_on, overlay, canvas, border, horizontal_line, vertical_line   # Atgriež mainīgos.

# Funkcija, kas izdzēš ekrānuzņēmuma rāmi.
def delete_border():
    global border_on, overlay, canvas, border, horizontal_line, vertical_line   # Izsauc jau definētos mainīgos.
    
    # Izdzēš rāmi no zīmēšanas virsmas.
    canvas.delete(border)
    canvas.delete(horizontal_line)
    canvas.delete(vertical_line)

    # Atjauno logu un norāda, ka ekrānuzņemuma rāmis nav uzzīmēts.
    overlay.update()
    border_on = False

    return border_on    # Atgriež mainīgos.

# Funkcija, kas savieno draw_border() un delete_border() funkcijas.
# "event=None" arguments ir vajadzīgs, lai to varētu lietot keyboard biblotēka, kas automātiski ievieto event argumentu funkcijās.
def toggle_border(event=None):
    global border_on, overlay, canvas, border, horizontal_line, vertical_line   # Izsauc jau definētos mainīgos.

    # Ja rāmis nav uz ekrāna, tad uzzīmē to. Ja ir, tad izdzēs to.
    if border_on == False:
        border_on, overlay, canvas, border, horizontal_line, vertical_line = draw_border()
    else:
        border_on = delete_border()

# Funkcija, kas veic ekrānuzņēmumu.
def capture(active_mode):
    global image_id_number_1, image_id_number_2, image_id_number_3, image_id_number_4   # Izsauc jau definētos mainīgos.

    # Atbilstoši režīmam definē, kur jāsaglabā bilde un tās numuru.
    # Šis ir objektīvi vienkāršākais veids, kā šo paveikt.
    if active_mode == "first":
        folder_to_save = os.path.join("reljefa_modelis", "pilskalnu_teritorijas")
        image_id = image_id_number_1
        image_id_number_1 += 1
    elif active_mode == "second":
        folder_to_save = os.path.join("augstumliknu_reljefa_slipuma_modelis", "pilskalnu_teritorijas")
        image_id = image_id_number_2
        image_id_number_2 += 1
    elif active_mode == "third":
        folder_to_save = os.path.join("reljefa_slipuma_modelis", "pilskalnu_teritorijas")
        image_id = image_id_number_3
        image_id_number_3 += 1
    elif active_mode == "fourth":
        folder_to_save = os.path.dirname(os.path.abspath(__file__))
        image_id = image_id_number_4
        image_id_number_4 += 1

    screenshot = ImageGrab.grab(bbox=screenshot_coordinates)            # Veic ekrānuzņēmumu dotajās koordinātās.    
    screenshot_name = f"pilskalns_{image_id}.png"                       # Definē ekrānuzņēmuma faila vārdu.
    screenshot_path = os.path.join(folder_to_save, screenshot_name)     # Definē ekrānuzņēmuma faila lokāciju.
    screenshot.save(screenshot_path)                                    # Saglabā bildi definētajā lokācijā.

    return screenshot_name                                              # Atgriež atpakaļ definēto bildes vārdu.

# Funkcija, kas savieno capture(image_id_number), draw_border() un delete_border() funkcijas.
# "event=None" arguments ir vajadzīgs, lai to varētu lietot keyboard biblotēka, kas automātiski ievieto event argumentu funkcijās.
def take_screenshot(event=None):
    global border_on                                                    # Izsauc jau definētos mainīgos.
    
    # Atrod aktīvo režīmu. Šis tiek lietots, lai definētu capture(active_mode) funkcijas argumentu.
    for key, value in modes.items():
        if value == True:
            active_mode = key
            break

    # Ja rāmis ir redzams, tad pirms ekrānuzņēmuma to vajag izdzēst un pēc tam uzzīmēt atkal. Ja nav, tad tikai veic ekrānuzņēmumu.
    if border_on == True:
        border_on = delete_border()
        screenshot_name = capture(active_mode)
        border_on, overlay, canvas, border, horizontal_line, vertical_line = draw_border()
    else:
        screenshot_name = capture(active_mode)

    print(f"Tika veikts ekrānuzņēmums: {screenshot_name} {mode_numbers[active_mode]}. režīmā")          # Paskaidro koda terminālī, ka tika veikts ekrānuzņēmums.

# Definē 4 bilžu lokāciju režīmus un tiem atbilstošos taustiņus.
modes = {"first": True, "second": False, "third": False, "fourth": False}
mode_buttons = {first_mode_button: "first", second_mode_button: "second", third_mode_button: "third", fourth_mode_button: "fourth"}
mode_numbers = {"first": 1, "second": 2, "third": 3, "fourth": 4}

# Funkcijas, kas attiecīgi maina 4 bilžu lokāciju režīmus.
def toggle_mode(event=None):
    
    # Visus režīmus veido nepatiesus jebšu neaktīvus.
    for key in modes:
        modes[key] = False
    
    # Tikai to režīmu, kuram sakrīt attiecīgi nospiestais taustiņš, padara par patiešu jebšu aktīvu.
    mode_name = mode_buttons.get(event.name)
    modes[mode_name] = True

    # Ziņo koda terminālī aktīvo režīmu.
    print(f"Mainīts ekrānuzņēmuma lokācijas režīms uz: {event.name}")

# Savieno klaviatūras taustiņus ar funkcijām.
keyboard.on_press_key(screenshot_button, take_screenshot)
keyboard.on_press_key(border_button, toggle_border)

for key in mode_buttons:
    keyboard.on_press_key(key, toggle_mode)

# Gaida piefiksētos taustiņus un izsauc attiecīgās funkcijas.
keyboard.wait()