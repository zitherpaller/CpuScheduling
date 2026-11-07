"""
OS//SIM - Operating System Simulator (Main Menu, pixel-game style)
------------------------------------------------------------------
Run with:  python main.py

HOW THIS PROGRAM IS ORGANIZED
  * This file (main.py) only builds the MAIN MENU and the window around it.
  * Each simulation (CPU Scheduling, Paging, etc.) goes in its own file
    inside a folder called `modules/`, for example modules/cpu_scheduling.py
  * Every module file must contain a class named `Module`, like this:

        class Module(ttk.Frame):
            def __init__(self, parent):
                super().__init__(parent)
                ...  # put your buttons, tables, inputs here

  * If a module file doesn't exist yet, the menu shows a "STAGE LOCKED"
    page instead of crashing, so you can build the modules one at a time.

TKINTER BASICS (the library used for the window)
  * tk.Tk        -> the main window
  * tk.Frame     -> an invisible box that holds other widgets
  * tk.Label     -> a piece of text
  * tk.Canvas    -> a drawing area (used for the pixel art and buttons)
  * .pack() / .grid() -> place a widget inside its parent
"""


import importlib          
import random             
import tkinter as tk      
from tkinter import ttk, messagebox, font as tkfont


# ---------- palette (colours) ----------
# Colours are written as hex codes: "#RRGGBB" (red, green, blue).
# We store them in variables (CAPITAL letters = "constant, don't change")
# so we can reuse them everywhere and change the whole theme in one place.
BG = "#1a1c2c"            # main background (dark navy)
PANEL = "#333c57"         # slightly lighter boxes
PANEL_HOVER = "#41507a"   # panel colour when the mouse is over it
SHADOW = "#0f101a"        # the hard "drop shadow" under buttons
BORDER = "#f4f4f4"        # outlines
TEXT = "#f4f4f4"          # normal text (off-white)
MUTED = "#94b0c2"         # softer, greyer text
HILITE = "#566c86"        # dim highlights
YELLOW = "#ffcd75"
ORANGE = "#ef7d57"
BLUE_DK = "#29366f"

# The list of modules. Each entry is a "tuple" of 4 things:
# (name shown on screen, file name inside modules/, short description, colour)
# To add a new module later, just add one more line to this list.
MODULES = [
    ("CPU Scheduling", "cpu_scheduling", "FCFS . SJF . SRT . ROUND ROBIN", "#41a6f6"),
    ("Banker's Algorithm", "bankers", "NEED . SAFE STATE . SAFE SEQUENCE", "#ef7d57"),
    ("Paging", "paging", "PAGE TO FRAME . ADDRESS TRANSLATION", "#c9a0ff"),
    ("Page Replacement", "page_replacement", "FIFO . LRU . OPTIMAL . HITS . FAULTS", "#a7f070"),
    ("Segmentation", "segmentation", "SEGMENT TABLE . BASE AND LIMIT", "#ffcd75"),
    ("Fragmentation", "fragmentation", "INTERNAL AND EXTERNAL FRAGMENTATION", "#ff6b81"),
    ("Disk Scheduling", "disk_scheduling", "SERVICE ORDER . HEAD MOVEMENT", "#73eff7"),
    ("Multiprogramming", "multiprogramming", "SHARED MEMORY . CPU UTILIZATION", "#f4a6c8"),
]

# The font used everywhere. This is just a starting value; when the app
# starts, it gets replaced by the best monospace font found on your computer.
FONT_NAME = "Courier New"


def F(size, bold=True):
    """Shortcut that builds a font setting, e.g. F(12) -> (fontname, 12, 'bold').
    tkinter wants fonts as (name, size, style), so this saves us typing."""
    return (FONT_NAME, size, "bold" if bold else "normal")


def pick_mono_font(root):
    """Look through the fonts installed on this computer and return the first
    good monospace one from our wish-list (monospace = every letter is the
    same width, which looks more 'retro game')."""
    available = set(tkfont.families(root))
    for name in ("Cascadia Mono", "Consolas", "Menlo", "DejaVu Sans Mono", "Courier New"):
        if name in available:
            return name
    return "Courier"  # last resort, almost every system has this


def lighten(hex_color, amount=0.25):
    """Make a colour lighter by mixing it with white. Used for hover effects.
    Example: lighten("#41a6f6") returns a paler blue."""
    # Split "#rrggbb" into three numbers (red, green, blue), each 0-255.
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    # Move each number part of the way toward 255 (white).
    r, g, b = (int(c + (255 - c) * amount) for c in (r, g, b))
    # Turn the numbers back into a "#rrggbb" string.
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------- pixel art
# Pixel art is stored as rows of text: "#" means "draw a square here",
# "." means "leave empty". This is a tiny 5-wide, 7-tall font that we
# use to draw the big title (we only defined the letters the title needs).
GLYPHS = {
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
}

# An 8x8 padlock picture, drawn the same way. Shown on locked pages.
LOCK = [
    "..####..",
    ".#....#.",
    ".#....#.",
    "########",
    "########",
    "###..###",
    "###..###",
    "########",
]

# The title letters take turns using these colours.
TITLE_COLORS = ["#ffcd75", "#41a6f6", "#a7f070", "#ef7d57", "#73eff7", "#f4a6c8"]


def draw_bitmap(canvas, rows, x, y, px, color):
    """Draw one picture (a list of text rows like GLYPHS) onto a canvas.
    x, y = top-left corner, px = size of each 'pixel' square on screen."""
    for r, row in enumerate(rows):            # r = row number (0, 1, 2...)
        for c, bit in enumerate(row):         # c = column number, bit = "#" or "."
            if bit == "#":
                # Draw one filled square for this pixel.
                canvas.create_rectangle(x + c * px, y + r * px,
                                        x + (c + 1) * px, y + (r + 1) * px,
                                        fill=color, outline="")


def draw_pixel_text(canvas, text, cx, y, px, colors, shadow_color):
    """Draw a word using the pixel font, centred horizontally on cx,
    with a blocky shadow behind it."""
    # Work out the total width (in pixel columns) so we can centre the text.
    # Letters are 5 columns wide, spaces 3, plus a 1-column gap between items.
    cols = sum(3 if ch == " " else 5 for ch in text) + (len(text) - 1)
    x0 = cx - cols * px // 2          # left edge of the whole word
    offset = max(2, px // 2)          # how far the shadow sits from the letters
    # We draw twice: first all the shadows, then all the letters on top.
    # (Doing shadows first keeps them from covering neighbouring letters.)
    for layer in ("shadow", "main"):
        x, ci = x0, 0                 # x = current position, ci = colour number
        for ch in text:
            if ch == " ":
                x += 4 * px           # a space: just skip ahead
                continue
            color = shadow_color if layer == "shadow" else colors[ci % len(colors)]
            dx = offset if layer == "shadow" else 0
            draw_bitmap(canvas, GLYPHS[ch], x + dx, y + dx, px, color)
            x += 6 * px               # move to where the next letter starts
            ci += 1                   # next letter gets the next colour


class PixelButton(tk.Canvas):
    """A chunky arcade-style button with a hard shadow that 'presses down'.

    A CLASS is a blueprint for making objects. Here, every time we write
    PixelButton(...), Python builds one button using this blueprint.
    (tk.Canvas in the brackets means: start from a Canvas and add our stuff.)
    """
    S = 5  # how many pixels the shadow sticks out

    def __init__(self, parent, label, command, color, width=440, height=84,
                 number=None, desc=None, size=13, bg=BG):
        # __init__ runs automatically when a new button is created.
        # "self" means "this particular button".
        # First, set up the Canvas part of the button.
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, cursor="hand2")
        # Remember the settings so the other methods can use them later.
        self.command = command        # the function to run when clicked
        self.w, self.h = width, height
        self.numbered = number is not None   # True for the big stage buttons
        self.color = color
        self._pressed = False         # is the mouse button currently held down?
        S, w, h = self.S, width, height
        mid = (h - S) / 2             # vertical middle of the button face

        # 1) the shadow: a dark rectangle shifted down and to the right
        self.create_rectangle(S, S, w, h, fill=SHADOW, outline="")
        # 2) the button face. tags="face" labels it so we can move every
        #    "face" item together when the button is pressed.
        self.base_fill = PANEL if self.numbered else color
        self.body = self.create_rectangle(2, 2, w - S, h - S, fill=self.base_fill,
                                          outline=BORDER, width=3, tags="face")
        if self.numbered:
            # Big stage button: coloured number block + name + description.
            self.create_rectangle(5, 5, 53, h - S - 3, fill=color, outline="", tags="face")
            self.create_text(29, mid, text=f"{number:02d}", fill=BG, font=F(16), tags="face")
            self.create_text(68, mid - (12 if desc else 0), text=label.upper(),
                             fill=TEXT, font=F(size), anchor="w", tags="face")
            if desc:
                self.create_text(68, mid + 14, text=desc, fill=MUTED,
                                 font=F(9, False), anchor="w", tags="face")
        else:
            # Small button (Back / Quit): just centred text on a coloured face.
            self.create_text((w - S) / 2, mid, text=label.upper(), fill=BG,
                             font=F(size), tags="face")
        # A ">" arrow on the right that only appears on hover (hidden for now).
        self.arrow = self.create_text(w - S - 24, mid, text=">", fill=color,
                                      font=F(18), state="hidden", tags="face")

        # "bind" connects a mouse event to one of our methods below.
        self.bind("<Enter>", self._enter)               # mouse moves onto button
        self.bind("<Leave>", self._leave)               # mouse moves off button
        self.bind("<ButtonPress-1>", self._press)       # left click pressed down
        self.bind("<ButtonRelease-1>", self._release)   # left click let go

    def _enter(self, _):
        # Mouse is over the button: brighten it and show the arrow.
        # ("_" is the event info tkinter sends us; we don't need it here.)
        fill = PANEL_HOVER if self.numbered else lighten(self.color)
        self.itemconfig(self.body, fill=fill)
        self.itemconfig(self.arrow, state="normal")

    def _leave(self, _):
        # Mouse left: go back to normal colour and hide the arrow.
        self.itemconfig(self.body, fill=self.base_fill)
        self.itemconfig(self.arrow, state="hidden")
        if self._pressed:                 # dragged away while holding the click
            self.move("face", -3, -3)     # pop the button back up
            self._pressed = False

    def _press(self, _):
        # Mouse button down: shift the face 3px down-right, so it looks like
        # it sank into its shadow.
        if not self._pressed:
            self.move("face", 3, 3)
            self._pressed = True

    def _release(self, e):
        # Mouse button up: pop the button back up, and if the mouse is still
        # on the button, run the function we were given (that's the "click").
        if not self._pressed:
            return
        self.move("face", -3, -3)
        self._pressed = False
        if 0 <= e.x <= self.w and 0 <= e.y <= self.h and self.command:
            self.command()


class TitleBar(tk.Canvas):
    """The top banner: a twinkling starfield with the pixel-art title."""

    def __init__(self, parent, height=170):
        super().__init__(parent, height=height, bg=BG, highlightthickness=0)
        self.h = height
        # Make 45 stars. Each is (x as 0-1 fraction, y as 0-1 fraction, size).
        # Using fractions means the stars still fit if the window is resized.
        self.stars = [(random.random(), random.random(), random.choice((3, 3, 4, 6)))
                      for _ in range(45)]
        self.items = []                       # the star shapes currently drawn
        self.bind("<Configure>", self.redraw) # redraw whenever the size changes
        self.after(450, self.twinkle)         # call twinkle() in 450 milliseconds

    def redraw(self, _=None):
        self.delete("all")                    # wipe the canvas clean
        w = self.winfo_width()                # current width of the banner
        self.items = []
        # Draw every star as a tiny square.
        for fx, fy, s in self.stars:
            x, y = int(fx * w), int(fy * self.h)
            self.items.append(self.create_rectangle(
                x, y, x + s, y + s, fill=random.choice((HILITE, MUTED)), outline=""))
        # Draw the title on top of the stars, then the little subtitle.
        draw_pixel_text(self, "OS SIMULATOR", w // 2, 36, 7, TITLE_COLORS, BLUE_DK)
        self.create_text(w // 2, 126, text="- By Paller, Pasion, Balmaceda -", fill=MUTED, font=F(12))

    def twinkle(self):
        # Stop if this banner was already removed (when you leave the menu).
        if not self.winfo_exists():
            return
        # Pick 3 random stars and give them a new colour (BG = "turned off").
        for item in random.sample(self.items, min(3, len(self.items))):
            self.itemconfig(item, fill=random.choice((HILITE, MUTED, TEXT, BG)))
        self.after(400, self.twinkle)         # run again in 400 ms (a loop)


# ---------------------------------------------------------------- pages
class HomeFrame(tk.Frame):
    """The main menu page (title + eight stage buttons + quit)."""

    def __init__(self, parent, on_open, on_quit):
        # on_open and on_quit are FUNCTIONS handed to us by the app.
        # We call them when a button is clicked.
        super().__init__(parent, bg=BG)
        TitleBar(self).pack(fill="x")         # banner across the top

        tk.Label(self, text="SELECT A STAGE", bg=BG, fg=YELLOW,
                 font=F(14)).pack(pady=(6, 8))

        grid = tk.Frame(self, bg=BG)          # a box to hold the buttons
        grid.pack()
        # Loop over MODULES and make one button per entry.
        # enumerate gives us a counter i (0, 1, 2...) along with each item.
        for i, (label, mod, desc, color) in enumerate(MODULES):
            # "lambda m=mod: on_open(m)" is a tiny one-line function that
            # remembers WHICH module this button belongs to.
            PixelButton(grid, label, lambda m=mod: on_open(m), color, number=i + 1,
                        desc=desc).grid(row=i // 2, column=i % 2, padx=10, pady=7)
            # row = i // 2 (whole-number division) and column = i % 2 (remainder)
            # put the buttons in two columns: 0,1 / 2,3 / 4,5 / 6,7

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=50, pady=(12, 0))
        self.blink = tk.Label(footer, text="PRESS A STAGE TO START", bg=BG,
                              fg=MUTED, font=F(11))
        self.blink.pack(side="left")
        PixelButton(footer, "Quit", on_quit, ORANGE, width=130, height=46,
                    size=12).pack(side="right")
        self._on = True
        self.after(600, self._blink)          # start the blinking text

    def _blink(self):
        if not self.winfo_exists():
            return
        self._on = not self._on               # flip True <-> False
        # Hiding the text = painting it the same colour as the background.
        self.blink.config(fg=MUTED if self._on else BG)
        self.after(600, self._blink)


class LockedFrame(tk.Frame):
    """Shown when a module's file doesn't exist yet."""

    def __init__(self, parent, title, color):
        super().__init__(parent, bg=BG)
        canvas = tk.Canvas(self, width=100, height=100, bg=BG, highlightthickness=0)
        canvas.pack(pady=(80, 10))
        draw_bitmap(canvas, LOCK, 10, 10, 10, color)   # draw the padlock
        tk.Label(self, text="STAGE LOCKED", bg=BG, fg=color, font=F(22)).pack()
        tk.Label(self, text=f"{title.upper()} IS COMING SOON", bg=BG, fg=MUTED,
                 font=F(11)).pack(pady=8)


# ---------------------------------------------------------------- app
class OSSimulatorApp(tk.Tk):
    """The main window. Everything else lives inside it."""

    def __init__(self):
        super().__init__()                    # create the actual window
        global FONT_NAME                      # we want to CHANGE the variable at the top
        FONT_NAME = pick_mono_font(self)
        self.title("PPB - Operating System Simulator")   # text in the title bar
        self.geometry("1000x730")             # starting size: width x height
        self.minsize(960, 700)                # can't be resized smaller than this
        self.configure(bg=BG)
        self.page = None                      # the page currently on screen

        self._setup_styles()                  # set the colours for ttk widgets
        self._build_layout()                  # create the top bar + body area
        self.show_home()                      # start on the main menu

    # ttk widgets (used inside your modules) are styled through a "Style"
    # object. We set it up here once so every module matches this theme.
    def _setup_styles(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")               # "clam" is easy to recolour
        except tk.TclError:
            pass                              # if it isn't available, skip it
        # "." means "apply to every ttk widget"; then we customize each kind.
        s.configure(".", background=BG, foreground=TEXT, font=F(10, False),
                    bordercolor=BORDER, lightcolor=BG, darkcolor=BG, troughcolor=PANEL)
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=TEXT)
        # Extra named styles you can use in modules: ttk.Label(..., style="Title.TLabel")
        s.configure("Title.TLabel", font=F(18), foreground=YELLOW)
        s.configure("Sub.TLabel", foreground=MUTED)
        s.configure("TLabelframe", background=BG, bordercolor=HILITE)
        s.configure("TLabelframe.Label", background=BG, foreground=YELLOW, font=F(10))
        s.configure("TButton", background="#3b5dc9", foreground="white", padding=7,
                    bordercolor=BORDER, focuscolor="#3b5dc9", font=F(10))
        # s.map changes a style depending on the state (hovered / pressed).
        s.map("TButton", background=[("active", "#41a6f6"), ("pressed", "#29366f")])
        s.configure("TEntry", fieldbackground=PANEL, foreground=TEXT,
                    insertcolor=TEXT, bordercolor=HILITE)
        s.configure("TCombobox", fieldbackground=PANEL, background=PANEL,
                    foreground=TEXT, arrowcolor=YELLOW, bordercolor=HILITE)
        s.map("TCombobox", fieldbackground=[("readonly", PANEL)])
        s.configure("TSpinbox", fieldbackground=PANEL, foreground=TEXT,
                    arrowcolor=YELLOW, insertcolor=TEXT)
        s.configure("TCheckbutton", background=BG)
        s.configure("TRadiobutton", background=BG)
        # Treeview is the table widget you'll use to show results.
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, rowheight=26, bordercolor=HILITE)
        s.configure("Treeview.Heading", background=BLUE_DK, foreground=YELLOW,
                    font=F(10), relief="flat")
        s.map("Treeview", background=[("selected", "#3b5dc9")],
              foreground=[("selected", "white")])
        s.configure("TNotebook", background=BG, bordercolor=HILITE)
        s.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(12, 6))
        s.map("TNotebook.Tab", background=[("selected", BLUE_DK)],
              foreground=[("selected", YELLOW)])
        s.configure("Vertical.TScrollbar", background=HILITE, arrowcolor=TEXT)
        s.configure("Horizontal.TScrollbar", background=HILITE, arrowcolor=TEXT)
        # Colours for the pop-up list of a dropdown (Combobox).
        self.option_add("*TCombobox*Listbox.background", PANEL)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)

    def _build_layout(self):
        # The top bar is only shown while a module is open. It has the
        # "< BACK" button, the module's name, and a coloured line under it.
        self.topbar = tk.Frame(self, bg=PANEL)
        PixelButton(self.topbar, "< Back", self.show_home, YELLOW, width=130,
                    height=46, size=11, bg=PANEL).pack(side="left", padx=12, pady=8)
        self.top_title = tk.Label(self.topbar, text="", bg=PANEL, fg=TEXT, font=F(16))
        self.top_title.pack(side="left", padx=10)
        self.topline = tk.Frame(self, height=4, bg=YELLOW)

        # The body is the big area where pages (menu or modules) are placed.
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True)

    def _set_page(self, frame, title=None, color=YELLOW):
        """Swap whatever page is on screen for a new one.
        If a title is given, the top bar (with Back button) is shown too."""
        if self.page is not None:
            self.page.destroy()               # remove the old page
        self.page = frame
        if title:                             # a module page: show the top bar
            self.top_title.config(text=title.upper(), fg=color)
            self.topline.config(bg=color)
            self.topbar.pack(side="top", fill="x", before=self.body)
            self.topline.pack(side="top", fill="x", before=self.body)
        else:                                 # the main menu: hide the top bar
            self.topbar.pack_forget()
            self.topline.pack_forget()
        frame.pack(fill="both", expand=True)

    def show_home(self):
        # Build a fresh main menu page and show it.
        self._set_page(HomeFrame(self.body, self.open_module, self.confirm_quit))

    def open_module(self, mod_name):
        # Find this module's display name and colour in the MODULES list.
        label, color = next((l, c) for l, m, _, c in MODULES if m == mod_name)
        # "try / except" = "attempt this, and if something goes wrong,
        # handle the error instead of crashing the whole program".
        try:
            # Load the file modules/<mod_name>.py, then create its Module page.
            module = importlib.import_module(f"modules.{mod_name}")
            frame = module.Module(self.body)
        except ModuleNotFoundError as e:
            # Fall back to the locked page ONLY if the module file itself is
            # missing, not if the file exists but imports something that's missing.
            if e.name not in (f"modules.{mod_name}", "modules"):
                messagebox.showerror("Module error", f"{label} failed to load:\n{e}")
                return
            frame = LockedFrame(self.body, label, color)
        except Exception as e:  # any other bug inside a module
            # Show the error in a pop-up, but keep the app running.
            messagebox.showerror("Module error", f"{label} failed to load:\n{e}")
            return
        self._set_page(frame, label, color)

    def confirm_quit(self):
        # Ask "OK / Cancel"; only close the window if the user chose OK.
        if messagebox.askokcancel("Quit", "Close the simulator?"):
            self.destroy()


# This block runs only when you start THIS file directly (python main.py),
# not when another file imports it.
if __name__ == "__main__":
    OSSimulatorApp().mainloop()   # mainloop() keeps the window open and listening