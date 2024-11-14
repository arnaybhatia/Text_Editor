import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinter import font as tkfont  # Import font module
import sys  # Add sys to detect the platform

class TextEditor:
    def __init__(self, root):
        self.root = root
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
        self.text_area.pack(expand=True, fill='both')
        
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
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        self.root.config(menu=menu_bar)
    
    def bind_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-q>', lambda e: self.quit_app())
        self.root.bind('<Control-z>', lambda e: self.undo_edit())
        self.root.bind('<Control-y>', lambda e: self.redo_edit())

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

def main():
    root = tk.Tk()
    editor = TextEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()