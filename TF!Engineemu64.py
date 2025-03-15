import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class EmuAIGUI:
    def __init__(self, emulator):
        self.emu = emulator  # Reference to the emulator core
        self.root = tk.Tk()
        self.root.title("EmuAI - N64 Emulator")
        self._create_menu()
        self._create_main_panel()
        self._create_status_bar()
    
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open ROM", command=self._open_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        # System menu
        system_menu = tk.Menu(menubar, tearoff=0)
        system_menu.add_command(label="Reset", command=self.emu.reset, accelerator="F1")
        system_menu.add_command(label="Pause", command=self.emu.toggle_pause, accelerator="F2")
        system_menu.add_separator()
        system_menu.add_command(label="Save State", command=self.emu.save_state, accelerator="F5")
        system_menu.add_command(label="Load State", command=self.emu.load_state, accelerator="F7")
        system_menu.add_cascade(label="Current Save State", menu=tk.Menu(system_menu, tearoff=0))
        system_menu.add_separator()
        system_menu.add_command(label="Cheats...", command=self._open_cheat_dialog, accelerator="Ctrl+C")
        menubar.add_cascade(label="System", menu=system_menu)
        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        options_menu.add_command(label="Settings", command=self._open_settings)
        options_menu.add_command(label="Plugins...", command=self._open_plugin_config)
        menubar.add_cascade(label="Options", menu=options_menu)
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)
    
    def _create_main_panel(self):
        # Main panel can either show a ROM list or the game canvas
        self.main_frame = ttk.Frame(self.root, padding=5)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        # For simplicity, use a Treeview as a ROM list placeholder
        self.rom_list = ttk.Treeview(self.main_frame, columns=("Name",), show="headings")
        self.rom_list.heading("Name", text="ROM Name")
        self.rom_list.pack(fill=tk.BOTH, expand=True)
        # Populate with any known ROMs (this could be extended to scan a folder)
        # For now, just indicate user to open a ROM
        self.rom_list.insert("", "end", values=("No ROM loaded. Use File -> Open ROM.",))
    
    def _create_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        self.vi_var = tk.StringVar(value="VI/s: 0.0")
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        fps_label = ttk.Label(status_frame, textvariable=self.vi_var, anchor=tk.E)
        status_label.pack(side=tk.LEFT, padx=5)
        fps_label.pack(side=tk.RIGHT, padx=5)
    
    def _open_rom(self):
        rom_path = filedialog.askopenfilename(title="Select N64 ROM", filetypes=[("N64 ROMs", "*.z64 *.n64 *.v64")])
        if rom_path:
            self.status_var.set(f"Loading ROM: {rom_path}")
            self.rom_list.delete(*self.rom_list.get_children())  # clear list
            self.rom_list.insert("", "end", values=(f"Playing: {rom_path}",))
            self.emu.load_rom(rom_path)
            self.emu.start()  # start emulation loop
            self.status_var.set("Emulation started")
    
    def _open_cheat_dialog(self):
        # Placeholder for cheat dialog
        messagebox.showinfo("Cheats", "Cheat Manager UI goes here.")
    
    def _open_settings(self):
        # Placeholder for settings dialog
        messagebox.showinfo("Settings", "Settings dialog goes here.")
    
    def _open_plugin_config(self):
        # Placeholder for plugin configuration
        messagebox.showinfo("Plugins", "Plugin configuration UI goes here.")
    
    def _show_about(self):
        messagebox.showinfo("About", "EmuAI N64 Emulator\nPowered by Project64-style GUI and N64 core.")
