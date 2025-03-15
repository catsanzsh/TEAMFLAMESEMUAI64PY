import tkinter as tk
from tkinter import filedialog, messagebox

class EmulAI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EmulAI - Zero-Shot Emulator")
        self.geometry("800x600")
        
        # Main display area for game graphics
        self.canvas = tk.Label(self, text="No ROM loaded", bg="black", fg="white",
                                font=("Arial", 16), width=80, height=25, anchor="center")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Status/Log panel at bottom
        self.log = tk.Text(self, height=8, state="disabled", bg="#111", fg="#0f0")
        self.log.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Setup menu
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open ROM...", command=self.open_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        plugins_menu = tk.Menu(menubar, tearoff=0)
        # (We will populate this menu dynamically based on available plugins)
        menubar.add_cascade(label="Plugins", menu=plugins_menu)
        
        cheats_menu = tk.Menu(menubar, tearoff=0)
        cheats_menu.add_command(label="Cheats Manager", command=self.show_cheats)
        menubar.add_cascade(label="Cheats", menu=cheats_menu)
        
        library_menu = tk.Menu(menubar, tearoff=0)
        library_menu.add_command(label="ROM Catalogue", command=self.open_catalogue)
        menubar.add_cascade(label="Library", menu=library_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About EmulAI", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        # Initialize plugin system (load built-in plugins)
        self.plugins = []        # will hold plugin instances
        self.plugin_menu = plugins_menu  # reference to update plugin menu
        self.load_plugins()
        
        # Current ROM/game state
        self.current_rom = None
        self.current_game_id = None  # an identifier or name for the loaded game
    def log_message(self, text):
        """Append a message to the log panel."""
        self.log.config(state="normal")
        self.log.insert(tk.END, text + "\n")
        self.log.config(state="disabled")
        self.log.see(tk.END)
    def open_rom(self):
        # File selection dialog
        rom_path = filedialog.askopenfilename(title="Select ROM",
                                              filetypes=[("ROM Files", "*.nes *.smc *.n64 *.gba *.gb *.bin *.iso"), 
                                                         ("All Files", "*.*")])
        if not rom_path:
            return  # user canceled
        # Simulate loading screen
        self.canvas.config(text="Loading ROM...", bg="black")
        self.update()  # refresh GUI to show loading text immediately
        
        rom_name = rom_path.split("/")[-1]
        self.log_message(f"Loading ROM: {rom_name}")
        try:
            with open(rom_path, "rb") as f:
                rom_data = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load ROM:\n{e}")
            self.canvas.config(text="No ROM loaded")
            return
        
        # Identify game (simple approach: file name without extension)
        game_id = rom_name.rsplit(".", 1)[0]
        self.current_rom = rom_data
        self.current_game_id = game_id
        
        # Notify plugins that a ROM is loaded
        for plugin in self.plugins:
            try:
                plugin.on_rom_loaded(game_id, rom_data)
            except Exception as e:
                self.log_message(f"[Plugin {plugin.name}] Error in on_rom_loaded: {e}")
        
        # After loading, remove loading screen text
        self.canvas.config(text=f"Running: {game_id}", bg="black")
        self.log_message(f"Successfully loaded {game_id}.")
        # (In a real emulator, start the emulation loop or thread here)
        
    def show_cheats(self):
        # Open a simple cheats window (implemented later)
        CheatManagerWindow(self, self.current_game_id)
    def open_catalogue(self):
        # Open ROM Catalogue window (implemented later)
        CatalogueWindow(self)
    def show_about(self):
        messagebox.showinfo("About EmulAI", "EmulAI - A Zero-Shot AI-Powered Emulator\n"
                                           "Built with Python and Tkinter")
    def load_plugins(self):
        """Instantiate and register built-in plugins."""
        # Create instances of each plugin class and store them
        self.plugins = [
            RediscoveredPlugin(self),
            PersonalizerPlugin(self),
            WonderGraphicsPlugin(self),
            DebuggerPlugin(self)
        ]
        # Add each plugin to the Plugins menu with a checkbox to enable/disable
        for plugin in self.plugins:
            # All plugins enabled by default (Personalizer may enforce always-on for some games internally)
            self.plugin_menu.add_checkbutton(label=plugin.name, onvalue=True, offvalue=False,
                                             variable=plugin.enabled_var)
