from PIL import ImageGrab           # Veiks ekrānuzņēmumus.
import tkinter as tk                # Uzzīmēs ekrānuzņēmuma rāmi uz ekrāna.
import keyboard                     # Iegūs klaviatūras inputu.

# Attiecīgā ekrāna px dimensijas. Šis ir vajadzīgi, lai atrastu ekrāna centru.
screen_width = 1920
screen_height = 1200

# Cik liels būs ekrānuzņēmuma garums un platums px.
square_size = 512 

# Atrod, kur jāuzņem ekrānuzņēmumus, lai bilde būtu ekrāna centrā.
screenshot_x = (screen_width - square_size) // 2
screenshot_y = (screen_height - square_size) // 2
screenshot_coordinates = (screenshot_x, screenshot_y, screenshot_x + square_size, screenshot_y + square_size)

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

# Funkcijas, kas uzzīmē rāmi uz ekrāna.
def draw_border():
    global border_on, overlay, canvas, border                       # Izsauc jau definētos mainīgos.

    if overlay == None:                                             # Šis nosacījums ir vajadzīgs, lai veidotu logu un zīmešanas virsmu tikai pirmaja reizē, kad šī funkcija tiek izsaukta.
        overlay = tk.Tk()                                           # Izveido jaunu logu.

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

        # Uzzīmē rāmi. Dod rāmim "border" identifikatoru.
        border = canvas.create_rectangle(screenshot_x, screenshot_y, screenshot_x + square_size, screenshot_y + square_size, outline="#ffffff", width=3, tags="border")

        # Veido, lai programma nereģistrē lietotāja peles darbības, kas ir virzītas uz rāmja.
        canvas.itemconfigure("border", state="disabled")

        # Attēlo logu un norāda, ka ekrānuzņemuma rāmis ir uzzīmēts.
        overlay.update()                            
        border_on = True
        
        return border_on, overlay, canvas, border   # Atgriež mainīgos.
    else:
        # Ja logs jau ir izveidots, nevajag definēt vēl vienu logu un zīmēšanas virsmu, bet gan tikai jaunu rāmi.

        # Uzzīmē rāmi.
        border = canvas.create_rectangle(screenshot_x, screenshot_y, screenshot_x + square_size, screenshot_y + square_size, outline="#ffffff", width=3)
        
        # Atjauno logu un norāda, ka ekrānuzņemuma rāmis ir uzzīmēts.
        overlay.update()                            
        border_on = True

        return border_on, overlay, canvas, border   # Atgriež mainīgos.

# Funkcija, kas izdzēš ekrānuzņēmuma rāmi.
def delete_border():
    global border_on, overlay, canvas, border   # Izsauc jau definētos mainīgos.
    
    canvas.delete(border)                       # Izdzēš rāmi no zīmēšanas virsmas.

    # Atjauno logu un norāda, ka ekrānuzņemuma rāmis nav uzzīmēts.
    overlay.update()
    border_on = False

    return border_on                            # Atgriež mainīgos.

# Funkcija, kas savieno capture(image_id_number), draw_border() un delete_border() funkcijas.
# "event=None" arguments ir vajadzīgs, lai to varētu lietot keyboard biblotēka, kas automātiski ievieto event argumentu funkcijās.
def take_screenshot(event=None):
    global image_id_number, border_on           # Izsauc jau definētos mainīgos.

    # Ja rāmis ir redzams, tad pirms ekrānuzņēmuma to vajag izdzēst un pēc tam uzzīmēt atkal. Ja nav, tad tikai veic ekrānuzņēmumu.
    if border_on == True:
        border_on = delete_border()
        image_id_number, screenshot_name = capture(image_id_number)
        border_on, overlay, canvas, border = draw_border()
    else:
        image_id_number, screenshot_name = capture(image_id_number)
    
    print(f"Tika veikts ekrānuzņēmums: {screenshot_name}")          # Paskaidro koda terminālī, ka tika veikts ekrānuzņēmums

# Funkcija, kas savieno draw_border() un delete_border() funkcijas.
# "event=None" arguments ir vajadzīgs, lai to varētu lietot keyboard biblotēka, kas automātiski ievieto event argumentu funkcijās.
def toggle_border(event=None):
    global border_on, overlay, canvas, border   # Izsauc jau definētos mainīgos.

    # Ja rāmis nav uz ekrāna, tad uzzīmē to. Ja ir, tad izdzēs to.
    if border_on == False:
        border_on, overlay, canvas, border = draw_border()
    else:
        border_on = delete_border()

# Savieno klaviatūras taustiņus ar funkcijām.[]
keyboard.on_press_key(screenshot_button, take_screenshot)
keyboard.on_press_key(border_button, toggle_border)

# Gaida piefiksētos taustiņus un izsauc attiecīgās funkcijas.
keyboard.wait()