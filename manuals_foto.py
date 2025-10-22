from PIL import ImageGrab           # Veiks ekrānuzņēmumus.
import tkinter as tk                # Uzzīmēs ekrānuzņēmuma rāmi uz ekrāna.
import keyboard                     # Iegūs klaviatūras inputu.
import win32gui, win32con           # Ļauj veidot pilnīgi nekustīgus, caurspīdīgus programmas logus.

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

image_id_number = 1                     # Palīdzēs katrai bildei dot savu numuru faila vārdā.
border_on = False                       # Norādīs, vai ekrānuzņēmuma rāmi vajag attēlot uz ekrāna.
screenshot_button = "["                 # Definē ar kuru pogu uz klaviatūras tiks veikts ekrānuzņēmums.
border_button = "]"                     # Definē ar kuru pogu uz klaviatūras var atvērt vai aizvērt ekrānuzņēmuma rāmi.                                                         

# Paskaidro programmas nosacījumus koda terminālī.
print(f'\nLai veiktu ekrānuzņēmumu, nospiediet "{screenshot_button}" pogu.')
print(f'Lai atvērtu vai aizvērtu ekrānuzņēmuma rāmi, nospiediet "{border_button}" pogu.\n')

# Funkcija, kas veic ekrānuzņēmumu.
def capture(image_id_number):
    screenshot = ImageGrab.grab(bbox=screenshot_coordinates)    # Veic ekrānuzņēmumu dotajās koordinātās.
    screenshot_name = f"pilskalns_{image_id_number}.png"        # Definē ekrānuzņēmuma bildes vārdu.
    screenshot.save(screenshot_name)                            # Saglabā bildi.
    image_id_number += 1                                        # Palielina id numuru par vienu vienību.

    return image_id_number, screenshot_name                     # Atgriež atpakaļ jauno id numura vērtību un definēto bildes vārdu.

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

# Funkcija, kas savieno capture(image_id_number), draw_border() un delete_border() funkcijas.
# "event=None" arguments ir vajadzīgs, lai to varētu lietot keyboard biblotēka, kas automātiski ievieto event argumentu funkcijās.
def take_screenshot(event=None):
    global image_id_number, border_on                               # Izsauc jau definētos mainīgos.

    # Ja rāmis ir redzams, tad pirms ekrānuzņēmuma to vajag izdzēst un pēc tam uzzīmēt atkal. Ja nav, tad tikai veic ekrānuzņēmumu.
    if border_on == True:
        border_on = delete_border()
        image_id_number, screenshot_name = capture(image_id_number)
        border_on, overlay, canvas, border, horizontal_line, vertical_line = draw_border()
    else:
        image_id_number, screenshot_name = capture(image_id_number)
    
    print(f"Tika veikts ekrānuzņēmums: {screenshot_name}")          # Paskaidro koda terminālī, ka tika veikts ekrānuzņēmums

# Funkcija, kas savieno draw_border() un delete_border() funkcijas.
# "event=None" arguments ir vajadzīgs, lai to varētu lietot keyboard biblotēka, kas automātiski ievieto event argumentu funkcijās.
def toggle_border(event=None):
    global border_on, overlay, canvas, border, horizontal_line, vertical_line   # Izsauc jau definētos mainīgos.

    # Ja rāmis nav uz ekrāna, tad uzzīmē to. Ja ir, tad izdzēs to.
    if border_on == False:
        border_on, overlay, canvas, border, horizontal_line, vertical_line = draw_border()
    else:
        border_on = delete_border()

# Savieno klaviatūras taustiņus ar funkcijām.[]
keyboard.on_press_key(screenshot_button, take_screenshot)
keyboard.on_press_key(border_button, toggle_border)

# Gaida piefiksētos taustiņus un izsauc attiecīgās funkcijas.
keyboard.wait()