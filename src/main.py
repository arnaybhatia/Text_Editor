import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinter import font as tkfont  # Import font module
import sys  # Add sys to detect the platform
import themes  # Import the themes module
import threading  # For autosave
import time
import enchant  # Import enchant for spell checking

class TextEditor:
    def __init__(self, root):
        # Set window size and position
        self.root.title("✍️ Simple Text Editor")
        # Set window size and position
        self.root.geometry("1000x600")
        self.root.minsize(400, 300)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')
        
        # Create toolbar
        self.create_toolbar()
        
        # Initialize default font settings
        self.current_font_family = 'Consolas'
        self.current_font_size = 11
        self.text_font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)
        
        # Initialize themes
        self.current_theme = themes.default_theme
        self.apply_theme(self.current_theme)
        
        # Create line number canvas
        self.line_numbers = tk.Text(
            self.main_frame, width=4, padx=3, takefocus=0, border=0,
            background='lightgrey', state='disabled', wrap='none'
        )
        self.line_numbers.pack(side='left', fill='y')
        
        # Create text area with custom font and colors
        self.text_area = tk.Text(
            self.main_frame,
            wrap='word',
            undo=True,
            font=self.text_font,
            bg='white',
            fg='black',
            insertbackground='black',
            selectbackground='#0078d7',
            selectforeground='white',
            padx=5,
            pady=5
        )
        self.text_area.pack(side='right', expand=True, fill='both')
        
        # Bind events for line numbers, syntax highlighting, and bracket matching
        self.text_area.bind('<KeyRelease>', self.on_key_release)
        self.text_area.bind('<Return>', self.auto_indent)
        self.text_area.bind('<Key>', self.match_brackets)
        self.text_area.bind('<MouseWheel>', self.sync_scroll)
        self.text_area.bind('<Button-1>', self.sync_scroll)
        self.text_area.bind('<Configure>', self.sync_scroll)
        
        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(self.text_area, orient='vertical', command=self.text_area.yview)
        self.scrollbar.pack(side='right', fill='y')
        self.text_area.config(yscrollcommand=self.scrollbar.set)
        
        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", anchor='w')
        self.status_bar.pack(side='bottom', fill='x')
        
        self.create_menu()
        self.bind_shortcuts()
        if sys.platform == 'darwin':
            self.bind_mac_shortcuts()
        
        # Start autosave
        self.autosave_interval = 300  # 5 minutes
        self.start_autosave()
        
        # Initialize spell checker
        self.spell_checker = enchant.Dict("en_US")
        
        # Initialize context menu for spell check
        self.create_spellcheck_menu()
        
    def create_toolbar(self):
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(side='top', fill='x')
        
        btn_new = ttk.Button(toolbar, text="New", command=self.new_file)
        btn_new.pack(side='left', padx=2, pady=2)
        
        btn_open = ttk.Button(toolbar, text="Open", command=self.open_file)
        btn_open.pack(side='left', padx=2, pady=2)
        
        btn_save = ttk.Button(toolbar, text="Save", command=self.save_file)
        btn_save.pack(side='left', padx=2, pady=2)
        
        # Add font family dropdown
        common_fonts = ['Arial', 'Calibri', 'Times New Roman', 'Courier New', 'Helvetica', 'Consolas']
        self.font_family_var = tk.StringVar(value=self.current_font_family)
        font_family_menu = ttk.Combobox(toolbar, textvariable=self.font_family_var, values=common_fonts, state='readonly')
        font_family_menu.pack(side='left', padx=5)
        font_family_menu.bind("<<ComboboxSelected>>", self.change_font_family)
        
        # Add font size dropdown
        self.font_size_var = tk.IntVar(value=self.current_font_size)
        font_size_menu = ttk.Combobox(toolbar, textvariable=self.font_size_var, values=tuple(range(8, 72, 2)), width=3, state='readonly')
        font_size_menu.pack(side='left', padx=5)
        font_size_menu.bind("<<ComboboxSelected>>", self.change_font_size)
        
        # Add bold, italic, underline buttons
        bold_btn = ttk.Button(toolbar, text="B", command=self.toggle_bold)
        bold_btn.pack(side='left', padx=2)
        italic_btn = ttk.Button(toolbar, text="I", command=self.toggle_italic)
        italic_btn.pack(side='left', padx=2)
        underline_btn = ttk.Button(toolbar, text="U", command=self.toggle_underline)
        underline_btn.pack(side='left', padx=2)
        
    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        
        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        accel_new = 'Ctrl+N'
        accel_open = 'Ctrl+O'
        accel_save = 'Ctrl+S'
        accel_exit = 'Ctrl+Q'
        accel_undo = 'Ctrl+Z'
        accel_redo = 'Ctrl+Y'
        if sys.platform == 'darwin':
            accel_new = 'Cmd+N'
            accel_open = 'Cmd+O'
            accel_save = 'Cmd+S'
            accel_exit = 'Cmd+Q'
            accel_undo = 'Cmd+Z'
            accel_redo = 'Cmd+Shift+Z'
        file_menu.add_command(label="New", command=self.new_file, accelerator=accel_new)
        file_menu.add_command(label="Open", command=self.open_file, accelerator=accel_open)
        file_menu.add_command(label="Save", command=self.save_file, accelerator=accel_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app, accelerator=accel_exit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit Menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo_edit, accelerator=accel_undo)
        edit_menu.add_command(label="Redo", command=self.redo_edit, accelerator=accel_redo)
        accel_find = 'Ctrl+F'
        accel_replace = 'Ctrl+H'
        if sys.platform == 'darwin':
            accel_find = 'Cmd+F'
            accel_replace = 'Cmd+H'
        edit_menu.add_command(label="Find", command=self.find_text, accelerator=accel_find)
        edit_menu.add_command(label="Replace", command=self.replace_text, accelerator=accel_replace)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # View Menu
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Light Theme", command=lambda: self.change_theme('default'))
        view_menu.add_command(label="Dark Theme", command=lambda: self.change_theme('dark'))
        menu_bar.add_cascade(label="View", menu=view_menu)
        
        self.root.config(menu=menu_bar)
        
        # Initialize spell check context menu
        self.create_spellcheck_menu()
    
    def bind_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-q>', lambda e: self.quit_app())
        self.root.bind('<Control-z>', lambda e: self.undo_edit())
        self.root.bind('<Control-y>', lambda e: self.redo_edit())
        self.root.bind('<Control-f>', lambda e: self.find_text())
        self.root.bind('<Control-h>', lambda e: self.replace_text())

    def bind_mac_shortcuts(self):
        self.root.bind('<Command-n>', lambda e: self.new_file())
        self.root.bind('<Command-o>', lambda e: self.open_file())
        self.root.bind('<Command-s>', lambda e: self.save_file())
        self.root.bind('<Command-q>', lambda e: self.quit_app())
        self.root.bind('<Command-z>', lambda e: self.undo_edit())
        self.root.bind('<Command-y>', lambda e: self.redo_edit())
    
    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.status_bar.config(text="New File")
    
    def open_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.END, file.read())
                self.root.title(f"✍️ Simple Text Editor - {file_path}")
                self.status_bar.config(text=f"Opened: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def save_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(self.text_area.get(1.0, tk.END))
                self.root.title(f"✍️ Simple Text Editor - {file_path}")
                self.status_bar.config(text=f"Saved: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {str(e)}")
    
    def quit_app(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.quit()
    
    def change_font_family(self, event=None):
        self.current_font_family = self.font_family_var.get()
        self.text_font.configure(family=self.current_font_family)

    def change_font_size(self, event=None):
        self.current_font_size = self.font_size_var.get()
        self.text_font.configure(size=self.current_font_size)

    def toggle_bold(self):
        current_weight = self.text_font.cget('weight')
        new_weight = 'normal' if current_weight == 'bold' else 'bold'
        self.text_font.configure(weight=new_weight)

    def toggle_italic(self):
        current_slant = self.text_font.cget('slant')
        new_slant = 'roman' if current_slant == 'italic' else 'italic'
        self.text_font.configure(slant=new_slant)

    def toggle_underline(self):
        current_underline = self.text_font.cget('underline')
        new_underline = 0 if current_underline == 1 else 1
        self.text_font.configure(underline=new_underline)

    def find_text(self):
        search_toplevel = tk.Toplevel(self.root)
        search_toplevel.title("Find")

        tk.Label(search_toplevel, text="Find:").grid(row=0, column=0, padx=4, pady=4)
        search_entry = tk.Entry(search_toplevel, width=30)
        search_entry.grid(row=0, column=1, padx=4, pady=4)
        search_entry.focus_set()

        def find():
            word = search_entry.get()
            self.text_area.tag_remove('found', '1.0', tk.END)
            if word:
                idx = '1.0'
                while True:
                    idx = self.text_area.search(word, idx, nocase=1, stopindex=tk.END)
                    if not idx:
                        break
                    lastidx = f'{idx}+{len(word)}c'
                    self.text_area.tag_add('found', idx, lastidx)
                    idx = lastidx
                self.text_area.tag_config('found', foreground='red', background='yellow')
            search_toplevel.destroy()
            self.status_bar.config(text=f"Found occurrences of '{word}'")

        tk.Button(search_toplevel, text="Find All", command=find).grid(row=1, column=0, columnspan=2, padx=4, pady=4)

    def replace_text(self):
        replace_toplevel = tk.Toplevel(self.root)
        replace_toplevel.title("Replace")

        tk.Label(replace_toplevel, text="Find:").grid(row=0, column=0, padx=4, pady=4)
        search_entry = tk.Entry(replace_toplevel, width=30)
        search_entry.grid(row=0, column=1, padx=4, pady=4)
        search_entry.focus_set()

        tk.Label(replace_toplevel, text="Replace:").grid(row=1, column=0, padx=4, pady=4)
        replace_entry = tk.Entry(replace_toplevel, width=30)
        replace_entry.grid(row=1, column=1, padx=4, pady=4)

        def replace():

            word = search_entry.get()
            replace_text = replace_entry.get()
            content = self.text_area.get('1.0', tk.END)
            new_content = content.replace(word, replace_text)
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', new_content)
            self.status_bar.config(text=f"Replaced '{word}' with '{replace_text}'")
            replace_toplevel.destroy()

        tk.Button(replace_toplevel, text="Replace All", command=replace).grid(row=2, column=0, columnspan=2, padx=4, pady=4)

    def undo_edit(self):
        try:
            self.text_area.edit_undo()
        except tk.TclError:
            pass
    
    def redo_edit(self):
        try:
            self.text_area.edit_redo()
        except tk.TclError:
            pass

    def apply_theme(self, theme):
        self.text_area.config(
            bg=theme['bg'], fg=theme['fg'], insertbackground=theme['cursor']
        )
        self.line_numbers.config(
            background=theme['line_bg'], foreground=theme['line_fg']
        )
        # ...apply theme to other widgets if needed...

    def change_theme(self, theme_name):
        if theme_name == 'default':
            self.current_theme = themes.default_theme
        elif theme_name == 'dark':
            self.current_theme = themes.dark_theme
        self.apply_theme(self.current_theme)

    def on_key_release(self, event=None):
        self.update_line_numbers()
        self.highlight_syntax()
        self.check_spelling()
    
    def match_brackets(self, event=None):
        # Remove existing bracket tags
        self.text_area.tag_remove('bracket', '1.0', tk.END)
        
        # Get the current cursor position
        pos = self.text_area.index(tk.INSERT)
        char = self.text_area.get(pos)
        brackets = {'(': ')', '{': '}', '[': ']', ')': '(', '}': '{', ']': '['}
        
        if (char in brackets):
            match = brackets[char]
            if char in '({[':
                direction = 'forward'
            else:
                direction = 'backward'
            count = 1
            idx = pos
            while True:
                if direction == 'forward':
                    idx = self.text_area.search(match, f"{idx}+1c", stopindex=tk.END)
                else:
                    idx = self.text_area.search(match, f"{idx}-1c", stopindex='1.0', backwards=True)
                if not idx:
                    break
                if self.text_area.get(idx) == char:
                    count += 1
                elif self.text_area.get(idx) == match:
                    count -= 1
                if count == 0:
                    break
            if idx:
                self.text_area.tag_add('bracket', pos, f"{pos}+1c")
                self.text_area.tag_add('bracket', idx, f"{idx}+1c")
                self.text_area.tag_config('bracket', foreground='red')
    
    def auto_indent(self, event=None):
        # Get the current line
        line = self.text_area.get("insert linestart", "insert")
        indent = ''
        for char in line:
            if char in (' ', '\t'):
                indent += char
            else:
                break
        if line.endswith(':'):
            indent += '    '  # Add 4 spaces for Python
        # Insert the indentation
        self.text_area.insert("insert", "\n" + indent)
        return 'break'
    
    def sync_scroll(self, event=None):
        self.line_numbers.yview_moveto(self.text_area.yview_moveto())
        self.line_numbers.update_idletasks()

    def update_line_numbers(self):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        line_count = self.text_area.index('end-1c').split('.')[0]
        line_numbers = "\n".join(str(i) for i in range(1, int(line_count)))
        self.line_numbers.insert(1.0, line_numbers)
        self.line_numbers.config(state='disabled')

    def highlight_syntax(self):
        # Clear existing tags
        self.text_area.tag_remove('keyword', '1.0', tk.END)
        self.text_area.tag_remove('misspelled', '1.0', tk.END)
        self.text_area.tag_remove('bracket', '1.0', tk.END)
        # Define keywords
        keywords = ['def', 'class', 'import', 'from', 'return', 'if', 'else', 'elif',
                    'for', 'while', 'try', 'except', 'with', 'as', 'pass', 'break', 'continue']
        # Apply highlighting
        for keyword in keywords:
            idx = '1.0'
            while True:
                idx = self.text_area.search(r'\b' + keyword + r'\b', idx, nocase=0,
                                            stopindex=tk.END, regexp=True)
                if not idx:
                    break
                lastidx = f'{idx}+{len(keyword)}c'
                self.text_area.tag_add('keyword', idx, lastidx)
                idx = lastidx
        # Configure tag styles
        self.text_area.tag_config('keyword', foreground='blue')
        self.text_area.tag_config('bracket', foreground='red')
        self.text_area.tag_config('misspelled', foreground='red', underline=1)
        # ...add more syntax rules as needed...

    def check_spelling(self):
        self.text_area.tag_remove('misspelled', '1.0', tk.END)
        words = self.text_area.get('1.0', 'end-1c').split()
        start_index = '1.0'
        for word in words:
            if not self.spell_checker.check(word):
                idx = self.text_area.search(word, start_index, nocase=1, stopindex=tk.END)
                if idx:
                    lastidx = f'{idx}+{len(word)}c'
                    self.text_area.tag_add('misspelled', idx, lastidx)
                    start_index = lastidx
        self.text_area.tag_config('misspelled', foreground='red', underline=1)
    
    def create_spellcheck_menu(self):
        self.spellcheck_menu = tk.Menu(self.root, tearoff=0)
        self.spellcheck_menu.add_command(label="Replace with...", command=self.replace_word)
        self.text_area.bind("<Button-3>", self.show_spellcheck_menu)
    
    def show_spellcheck_menu(self, event):
        index = self.text_area.index(f"@{event.x},{event.y}")
        if 'misspelled' in self.text_area.tag_names(index):
            self.spellcheck_menu.tk_popup(event.x_root, event.y_root)
    
    def replace_word(self):
        try:
            selection_start = self.text_area.index(tk.SEL_FIRST)
            selection_end = self.text_area.index(tk.SEL_LAST)
            misspelled_word = self.text_area.get(selection_start, selection_end)
            suggestions = self.spell_checker.suggest(misspelled_word)
            if suggestions:
                # Prompt user to select a suggestion
                suggestion = messagebox.askquestion("Replace", f"Replace '{misspelled_word}' with '{suggestions[0]}'?")
                if suggestion == 'yes':
                    self.text_area.delete(selection_start, selection_end)
                    self.text_area.insert(selection_start, suggestions[0])
                    self.status_bar.config(text=f"Replaced '{misspelled_word}' with '{suggestions[0]}'")
        except tk.TclError:
            pass  # No word selected

    def start_autosave(self):
        def autosave():
            while True:
                time.sleep(self.autosave_interval)
                self.save_backup()
        autosave_thread = threading.Thread(target=autosave, daemon=True)
        autosave_thread.start()

    def save_backup(self):
        backup_path = 'backup.txt'
        try:
            with open(backup_path, 'w') as backup_file:
                backup_file.write(self.text_area.get(1.0, tk.END))
            self.status_bar.config(text="Autosaved backup")
        except Exception as e:
            self.status_bar.config(text=f"Autosave failed: {str(e)}")

def main():
    root = tk.Tk()
    editor = TextEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()