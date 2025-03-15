import os
import importlib
import logging
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# Configure logging to file and console when running as main
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,  # Use DEBUG for detailed output; change to INFO for less verbosity
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler("emulai.log", mode='a'),
            logging.StreamHandler()
        ]
    )
logger = logging.getLogger(__name__)

class EmulAI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EmulAI Emulator")
        # Handle window close to ensure proper cleanup
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Initialize state
        self.current_rom = None
        self.current_game = None
        self.loading = False    # Flag to prevent concurrent ROM loads
        self.cheat_data = {}
        self.library_dir = None

        # Load persisted cheat data (if available)
        try:
            with open("cheats.json", "r") as f:
                self.cheat_data = json.load(f)
                logger.info(f"Loaded cheat data for {len(self.cheat_data)} game(s).")
        except FileNotFoundError:
            logger.info("No cheat data file found, starting with empty cheat list.")
            self.cheat_data = {}
        except Exception as e:
            logger.error(f"Failed to load cheat data: {e}")
            self.cheat_data = {}

        # Set up the menu bar
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open ROM...", command=self.open_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        # Plugins menu
        self.plugins_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plugins", menu=self.plugins_menu)

        # Cheats menu
        cheats_menu = tk.Menu(menubar, tearoff=0)
        cheats_menu.add_command(label="Manage Cheats", command=self.manage_cheats)
        menubar.add_cascade(label="Cheats", menu=cheats_menu)

        # Library menu
        library_menu = tk.Menu(menubar, tearoff=0)
        library_menu.add_command(label="Open Library", command=self.show_library)
        menubar.add_cascade(label="Library", menu=library_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About EmulAI", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Main content area (could be replaced with emulator display canvas)
        self.main_label = tk.Label(self, text="No ROM loaded.", anchor="center")
        self.main_label.pack(expand=True, fill=tk.BOTH)

        # Status bar at the bottom for messages
        self.status_var = tk.StringVar(value="Ready.")
        status_label = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor='w')
        status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Load plugins on startup
        self.plugins = {}
        self.load_plugins()

    def load_plugins(self):
        """Load all plugins from the plugins directory and update the Plugins menu."""
        # Determine plugin directory relative to this script
        try:
            base_dir = os.path.dirname(__file__)
        except NameError:
            base_dir = os.getcwd()
        plugin_dir = os.path.join(base_dir, "plugins")
        if not os.path.isdir(plugin_dir):
            logger.warning(f"Plugin directory not found: {plugin_dir}")
            # Still add the refresh option even if no directory
            self.plugins_menu.delete(0, tk.END)
            self.plugins_menu.add_command(label="Refresh Plugins", command=self.refresh_plugins_menu)
            return False

        # Ensure the plugins package is importable
        if base_dir not in os.sys.path:
            os.sys.path.insert(0, base_dir)

        # Clear any existing menu items (for refresh case)
        self.plugins_menu.delete(0, tk.END)
        self.plugins.clear()

        loaded_any = False
        for filename in sorted(os.listdir(plugin_dir)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            plugin_name = filename[:-3]
            module_name = f"plugins.{plugin_name}"
            try:
                # Import or reload the plugin module
                if module_name in importlib.util.sys.modules:
                    module = importlib.reload(importlib.util.sys.modules[module_name])
                else:
                    module = importlib.import_module(module_name)
                # Register or add plugin to menu
                if hasattr(module, "register"):
                    # Plugin provides its own registration function
                    module.register(self)
                    logger.info(f"Registered plugin: {plugin_name}")
                elif hasattr(module, "run"):
                    # Plugin provides a run() function, create a menu entry for it
                    display_name = plugin_name.replace('_', ' ').title()
                    if hasattr(module, "PLUGIN_NAME"):
                        display_name = getattr(module, "PLUGIN_NAME")
                    def plugin_callback(mod=module, name=display_name):
                        """Wrap the plugin run call with error handling."""
                        try:
                            mod.run(self)
                        except Exception as e:
                            logger.error(f"Error running plugin '{name}': {e}", exc_info=True)
                            messagebox.showerror("Plugin Error",
                                                 f"An error occurred in plugin '{name}':\n{e}")
                    self.plugins_menu.add_command(label=display_name, command=plugin_callback)
                    logger.info(f"Loaded plugin: {plugin_name} (added to menu as '{display_name}')")
                else:
                    logger.warning(f"Plugin '{plugin_name}' has no register() or run() function; skipped.")
                    continue
                # Store the module reference
                self.plugins[plugin_name] = module
                loaded_any = True
            except Exception as e:
                logger.error(f"Failed to load plugin '{plugin_name}': {e}", exc_info=True)
                messagebox.showerror("Plugin Load Error",
                                     f"Failed to load plugin '{plugin_name}':\n{e}")
        # Add the "Refresh Plugins" option at the end of the Plugins menu
        self.plugins_menu.add_separator()
        self.plugins_menu.add_command(label="Refresh Plugins", command=self.refresh_plugins_menu)
        return loaded_any

    def refresh_plugins_menu(self):
        """Reload the plugin list and update the Plugins menu."""
        logger.info("Refreshing plugins menu...")
        self.load_plugins()

    def open_rom(self):
        """Open a file dialog to select a ROM and load it."""
        rom_path = filedialog.askopenfilename(
            title="Select ROM File",
            filetypes=[("ROM files", "*.rom;*.nes;*.sfc;*.smc;*.gba;*.gb;*.gbc"), ("All files", "*.*")]
        )
        if rom_path:
            self.load_rom(rom_path)

    def load_rom(self, rom_path):
        """Load the given ROM file without freezing the UI."""
        if self.loading:
            messagebox.showinfo("Please wait", "A ROM is already loading. Please wait for it to finish.")
            return
        self.loading = True
        rom_name = os.path.basename(rom_path)
        # Update UI to indicate loading
        self.status_var.set(f"Loading ROM: {rom_name} ...")
        self.main_label.config(text=f"Loading ROM: {rom_name} ...")
        self.update_idletasks()
        # Perform the file load in a separate thread
        def load_task():
            success = False
            error = None
            try:
                # Simulate reading or processing the ROM file (replace with actual emulator logic as needed)
                with open(rom_path, "rb") as f:
                    _ = f.read()
                success = True
            except Exception as e:
                error = e
            # Once done, schedule the UI update back on the main thread
            self.after(0, lambda: self.on_rom_loaded(rom_path, success, error))
        threading.Thread(target=load_task, daemon=True).start()

    def on_rom_loaded(self, rom_path, success, error):
        """Handle the result of ROM loading (success or failure) on the main thread."""
        rom_name = os.path.basename(rom_path)
        if not success:
            # Loading failed
            logger.error(f"Failed to load ROM {rom_path}: {error}")
            messagebox.showerror("Error", f"Failed to load ROM:\n{error}")
            self.status_var.set("Failed to load ROM.")
            self.main_label.config(text="No ROM loaded.")
        else:
            # Loading succeeded
            self.current_rom = rom_path
            self.current_game = os.path.splitext(rom_name)[0]
            logger.info(f"ROM loaded successfully: {rom_path}")
            self.status_var.set(f"ROM loaded: {rom_name}")
            self.main_label.config(text=f"Loaded ROM: {rom_name}")
            # Update window title to show loaded game
            self.title(f"EmulAI - {rom_name}")
            # Log how many cheats are enabled for this game (if any)
            cheats_for_game = self.cheat_data.get(self.current_game, [])
            enabled_count = sum(1 for c in cheats_for_game if c.get("enabled"))
            if enabled_count:
                logger.info(f"{enabled_count} cheat(s) enabled for {self.current_game}.")
            # Refresh cheat manager UI if it's open
            if hasattr(self, "cheat_window") and self.cheat_window is not None:
                try:
                    self.cheat_window.update_cheats()
                except Exception as e:
                    logger.error(f"Could not refresh cheat window: {e}")
        # In all cases, reset loading flag
        self.loading = False

    def manage_cheats(self):
        """Open the Cheat Manager window to manage cheats for the current ROM."""
        if not self.current_game:
            messagebox.showinfo("No ROM Loaded", "Please load a ROM before managing cheats.")
            return
        # If the cheat window is already open, bring it to front
        if hasattr(self, "cheat_window") and self.cheat_window is not None:
            try:
                self.cheat_window.lift()
                return
            except Exception:
                # If it was closed without updating the reference
                self.cheat_window = None
        # Create a new cheat manager window
        self.cheat_window = CheatManager(self)
        # Ensure reference is cleared when window is closed
        self.cheat_window.protocol("WM_DELETE_WINDOW", lambda: self.close_cheat_window())

    def close_cheat_window(self):
        """Reset cheat_window reference after it's closed."""
        if self.cheat_window is not None:
            self.cheat_window.destroy()
            self.cheat_window = None

    def show_library(self):
        """Open the ROM Library window to browse and select games."""
        if hasattr(self, "library_window") and self.library_window is not None:
            try:
                self.library_window.lift()
                return
            except Exception:
                self.library_window = None
        self.library_window = LibraryWindow(self)
        self.library_window.protocol("WM_DELETE_WINDOW", lambda: self.close_library_window())

    def close_library_window(self):
        """Reset library_window reference after it's closed."""
        if self.library_window is not None:
            self.library_window.destroy()
            self.library_window = None

    def show_about(self):
        """Show an About dialog with basic information."""
        messagebox.showinfo(
            "About EmulAI",
            "EmulAI Emulator\nVersion 1.0\n\nA Tkinter-based emulator UI example."
        )

    def quit_app(self):
        """Exit the application, saving data and closing cleanly."""
        logger.info("Exiting EmulAI application.")
        # Save cheats to file for persistence
        try:
            with open("cheats.json", "w") as f:
                json.dump(self.cheat_data, f, indent=4)
            logger.info("Cheat data saved to cheats.json.")
        except Exception as e:
            logger.error(f"Error saving cheat data: {e}")
        self.destroy()

class CheatManager(tk.Toplevel):
    """Window for viewing and editing cheat codes for the current game."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title(f"Cheat Manager - {parent.current_game}")
        self.geometry("400x300")
        # Label to show which game's cheats are being managed
        game = parent.current_game or "None"
        lbl = tk.Label(self, text=f"Cheats for {game}")
        lbl.pack(pady=5)
        self.label = lbl

        # Listbox for cheat entries
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Double-click to toggle cheat enable/disable
        self.listbox.bind("<Double-Button-1>", lambda e: self.toggle_cheat())
        # Track selection to enable/disable Remove button accordingly
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_select())

        # Buttons for adding/removing cheats
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        add_btn = tk.Button(btn_frame, text="Add Cheat", command=self.add_cheat)
        add_btn.pack(side=tk.LEFT, padx=5)
        remove_btn = tk.Button(btn_frame, text="Remove Cheat", command=self.remove_cheat)
        remove_btn.pack(side=tk.LEFT, padx=5)
        close_btn = tk.Button(btn_frame, text="Close", command=self.close)
        close_btn.pack(side=tk.RIGHT, padx=5)
        self.add_button = add_btn
        self.remove_button = remove_btn
        # Initialize remove button state (no selection yet)
        self.remove_button.config(state=tk.DISABLED)

        # Populate the cheat list for the current game
        self.update_cheats()
        # If no game loaded (shouldn't happen since we check before opening), disable adding
        if not parent.current_game:
            self.add_button.config(state=tk.DISABLED)

    def update_cheats(self):
        """Refresh the cheat list display to match current cheats for the game."""
        game = self.parent.current_game
        if game:
            self.label.config(text=f"Cheats for {game}")
        else:
            self.label.config(text="Cheats for None")
        # Clear current list
        self.listbox.delete(0, tk.END)
        if not game:
            return
        cheats = self.parent.cheat_data.get(game, [])
        for cheat in cheats:
            status = "[X]" if cheat.get("enabled") else "[ ]"
            desc = cheat.get("desc", "")
            display_text = f"{status} {desc}"
            self.listbox.insert(tk.END, display_text)
        # Reset remove button state (will be enabled when user selects an item)
        self.remove_button.config(state=tk.DISABLED)

    def add_cheat(self):
        """Add a new cheat code for the current game."""
        game = self.parent.current_game
        if not game:
            return
        code = simpledialog.askstring("Add Cheat", "Enter cheat code:", parent=self)
        if code is None or code.strip() == "":
            return  # Cancelled or empty input
        desc = simpledialog.askstring("Add Cheat", "Enter cheat description:", parent=self)
        if desc is None or desc.strip() == "":
            return  # Cancelled or empty input
        # Create cheat entry (enabled by default)
        cheat = {"code": code, "desc": desc, "enabled": True}
        self.parent.cheat_data.setdefault(game, []).append(cheat)
        logger.info(f"Added cheat for {game}: \"{desc}\" [{code}]")
        self.update_cheats()

    def remove_cheat(self):
        """Remove the selected cheat from the current game's list."""
        sel = self.listbox.curselection()
        if not sel:
            return
        index = sel[0]
        game = self.parent.current_game
        if not game:
            return
        cheats = self.parent.cheat_data.get(game, [])
        if 0 <= index < len(cheats):
            removed = cheats.pop(index)
            logger.info(f"Removed cheat for {game}: \"{removed.get('desc', '')}\"")
            if not cheats:  # If no cheats left for the game, remove the key
                self.parent.cheat_data.pop(game, None)
            self.update_cheats()

    def toggle_cheat(self):
        """Toggle the enabled/disabled status of the selected cheat."""
        sel = self.listbox.curselection()
        if not sel:
            return
        index = sel[0]
        game = self.parent.current_game
        if not game:
            return
        cheats = self.parent.cheat_data.get(game, [])
        if 0 <= index < len(cheats):
            cheat = cheats[index]
            cheat['enabled'] = not cheat.get('enabled', False)
            status = "enabled" if cheat['enabled'] else "disabled"
            logger.info(f"Toggled cheat \"{cheat.get('desc', '')}\" for {game} ({status}).")
            self.update_cheats()

    def _on_select(self):
        """Enable the Remove button when a cheat is selected, otherwise disable it."""
        if self.listbox.curselection():
            self.remove_button.config(state=tk.NORMAL)
        else:
            self.remove_button.config(state=tk.DISABLED)

    def close(self):
        """Close the cheat manager window."""
        self.destroy()

class LibraryWindow(tk.Toplevel):
    """Window to display and manage a list of ROMs (game library)."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("ROM Library")
        self.geometry("400x300")
        # Listbox to list available ROM files
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox.bind("<Double-Button-1>", lambda e: self.open_selected())
        # Control buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        open_btn = tk.Button(btn_frame, text="Open ROM", command=self.open_selected)
        open_btn.pack(side=tk.LEFT, padx=5)
        refresh_btn = tk.Button(btn_frame, text="Refresh", command=self.refresh_list)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        close_btn = tk.Button(btn_frame, text="Close", command=self.close)
        close_btn.pack(side=tk.RIGHT, padx=5)

        # List to store full paths of ROM files for selection
        self.games = []
        # Populate the list on startup
        self.refresh_list(first_load=True)

    def refresh_list(self, first_load=False):
        """Refresh the ROM list from the library directory."""
        if first_load:
            # On first open, if directory not set, ask user to choose a folder
            if not self.parent.library_dir:
                dir_path = filedialog.askdirectory(title="Select ROMs Directory", parent=self)
                if not dir_path:
                    logger.info("Library directory selection cancelled.")
                    self.destroy()
                    self.parent.library_window = None
                    return
                self.parent.library_dir = dir_path
            # Use the existing directory if already chosen previously
            dir_path = self.parent.library_dir
        else:
            # For subsequent refresh calls, use the stored directory
            dir_path = self.parent.library_dir
            if not dir_path:
                logger.warning("No library directory set for refresh.")
                return

        # Clear current list
        self.listbox.delete(0, tk.END)
        self.games = []
        if not os.path.isdir(dir_path):
            logger.error(f"ROM Library directory not found: {dir_path}")
            return

        logger.info(f"Scanning ROM library directory: {dir_path}")
        # Filter for common ROM file extensions
        valid_exts = {'.rom', '.nes', '.sfc', '.smc', '.gba', '.gb', '.gbc'}
        try:
            for entry in sorted(os.listdir(dir_path)):
                full_path = os.path.join(dir_path, entry)
                if os.path.isdir(full_path):
                    continue
                ext = os.path.splitext(entry)[1].lower()
                if ext in valid_exts:
                    self.games.append(full_path)
                    self.listbox.insert(tk.END, entry)
            logger.info(f"Found {len(self.games)} ROM(s) in the library.")
        except Exception as e:
            logger.error(f"Error reading ROM library directory: {e}")

    def open_selected(self):
        """Load the selected ROM from the list."""
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select a ROM to open.")
            return
        index = sel[0]
        rom_path = self.games[index]
        logger.info(f"Opening ROM from library: {rom_path}")
        self.parent.load_rom(rom_path)

    def close(self):
        """Close the library window."""
        self.destroy()

# Run the application
if __name__ == "__main__":
    app = EmulAI()
    app.mainloop()
