import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyperclip
import json
import sys

class FileTreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClipMate")
        self.set_window_position(root, 600, 600)
        self.root.minsize(600, 300)
        
        # Set the application icon
        icon_path = self.resource_path('clipmate.png')
        self.icon = tk.PhotoImage(file=icon_path)
        self.root.iconphoto(True, self.icon)

        self.preferences_file = "preferences.json"
        self.preferences = self.load_preferences()

        # Show welcome message if not suppressed
        if not self.preferences.get("suppress_welcome", False):
            self.show_welcome_message()

        # Create a frame for the treeview and scrollbar
        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(expand=True, fill=tk.BOTH)

        # Create a treeview to display the file structure
        self.tree = ttk.Treeview(self.tree_frame, columns=("fullpath",), show="tree")
        self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Scrollbar for the treeview
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Frame for the buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(fill=tk.X, pady=5)

        # Button to select directory
        self.select_button = tk.Button(self.button_frame, text="Select Directory", command=self.select_directory, bg='light grey')
        self.select_button.pack(fill=tk.X, padx=5, pady=2)

        # Button to copy contents to clipboard
        self.copy_button = tk.Button(self.button_frame, text="Copy Contents to Clipboard", command=self.copy_to_clipboard, state=tk.DISABLED, bg='light grey')
        self.copy_button.pack(fill=tk.X, padx=5, pady=2)

        self.filepaths = {}

        # Bind selection event to update button state
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def resource_path(self, relative_path):
        """ Get the absolute path to the resource, works for dev and for PyInstaller. """
        try:
            # PyInstaller creates a temp folder and stores the app in a temp folder
            base_path = sys._MEIPASS
        except Exception:
            # Access directly when running in development mode
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def show_welcome_message(self):
        def on_ok():
            if suppress_var.get():
                self.preferences["suppress_welcome"] = True
                self.save_preferences()
            welcome_msg.destroy()

        welcome_msg = tk.Toplevel(self.root)
        welcome_msg.title("Welcome")
        welcome_msg.geometry("400x300")  # Increased height to ensure visibility of the button
        self.center_window(welcome_msg, 400, 300)
        welcome_msg.resizable(False, False)

        # Create a frame for the message content
        message_frame = tk.Frame(welcome_msg)
        message_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Create a Text widget for the message
        message_text = tk.Text(message_frame, wrap=tk.WORD, height=10, width=50, bd=0, bg=welcome_msg.cget("bg"), font=("Helvetica", 12))
        
        # Tag configurations for heading and centered text
        message_text.tag_configure("heading", font=("Helvetica", 16, "bold"), justify='center')
        message_text.tag_configure("centered", justify='center')

        # Insert text with tags
        message_text.insert(tk.END, "Welcome to ClipMate!\n\n", "heading")
        message_text.insert(tk.END, "ClipMate allows you to select a directory and then easily copy the contents of selected files and subdirectories to the clipboard. "
                                     "You can use this feature to quickly gather and share code from your projects for review or assistance.\n", "centered")
        
        message_text.configure(state=tk.DISABLED)
        message_text.grid(row=0, column=0, columnspan=2, pady=5, sticky="nsew")

        # Add a checkbox for suppressing the message
        suppress_var = tk.BooleanVar()
        checkbox = tk.Checkbutton(message_frame, text="Don't show this message again", variable=suppress_var)
        checkbox.grid(row=1, column=0, columnspan=2, pady=5, sticky="n")

        # Add Let's Go! button with adjusted font size and background color
        tk.Button(message_frame, text="Let's Go!", command=on_ok, font=("Helvetica", 12, "bold"), padx=20, pady=10, bg='light grey').grid(row=2, column=0, columnspan=2, pady=10)

        # Adjust row and column weights to expand widgets
        message_frame.grid_rowconfigure(0, weight=1)
        message_frame.grid_rowconfigure(1, weight=0)
        message_frame.grid_rowconfigure(2, weight=0)
        message_frame.grid_columnconfigure(0, weight=1)
        message_frame.grid_columnconfigure(1, weight=1)

        # Make the welcome message modal
        welcome_msg.transient(self.root)
        welcome_msg.grab_set()
        self.root.wait_window(welcome_msg)

    def set_window_position(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def center_window(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def load_preferences(self):
        if os.path.exists(self.preferences_file):
            with open(self.preferences_file, 'r') as f:
                return json.load(f)
        return {}

    def save_preferences(self):
        with open(self.preferences_file, 'w') as f:
            json.dump(self.preferences, f)

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.populate_tree(directory)

    def populate_tree(self, directory):
        self.tree.delete(*self.tree.get_children())
        self.filepaths = {}
        self._populate_tree("", directory, directory)

    def _populate_tree(self, parent, directory, base_directory):
        for item in os.listdir(directory):
            fullpath = os.path.join(directory, item)
            relative_path = os.path.relpath(fullpath, base_directory)
            node = self.tree.insert(parent, "end", text=item, open=False, values=(relative_path,))
            if os.path.isdir(fullpath):
                self._populate_tree(node, fullpath, base_directory)
            self.filepaths[node] = fullpath

    def copy_to_clipboard(self):
        contents = []
        for item in self.tree.selection():
            relative_path = self.tree.item(item, "values")[0]
            fullpath = self.filepaths[item]
            if os.path.isfile(fullpath):
                with open(fullpath, 'r', encoding='utf-8') as f:
                    contents.append(f"**{relative_path}**\n{f.read()}\n")
            elif os.path.isdir(fullpath):
                for root, _, files in os.walk(fullpath):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_file_path = os.path.relpath(file_path, fullpath)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            contents.append(f"**{relative_file_path}**\n{f.read()}\n")
        
        pyperclip.copy('\n'.join(contents))
        messagebox.showinfo("Success", "Selected file contents copied to clipboard!")

    def on_tree_select(self, event):
        # Enable the button if there's a selection
        if self.tree.selection():
            self.copy_button.config(state=tk.NORMAL)
        else:
            self.copy_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileTreeApp(root)
    root.mainloop()
