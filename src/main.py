import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinter import font as tkfont  # Import font module
import sys  # Add sys to detect the platform
import themes  # Import the themes module
import threading  # For autosave
import time

# Check for spell checker availability
try:
    import enchant
    SPELL_CHECK_ENABLED = True
except ImportError:
    SPELL_CHECK_ENABLED = False

class TextEditor:
    SPELL_CHECK_ENABLED = SPELL_CHECK_ENABLED  # Class attribute

    def __init__(self, root):
        self.root = root
        self.root.title("✍️ Simple Text Editor")
        self.root.geometry("1000x600")
        self.root.minsize(400, 300)
        
        # Initialize themes first
        self.current_theme = themes.default_theme
        
        # Configure ttk styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Initialize font settings before creating widgets
        self.current_font_family = 'Consolas'
        self.current_font_size = 11
        self.text_font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)
        
        # Configure common styles
        self.style.configure('Toolbar.TFrame', padding=1)
        self.style.configure('Tool.TButton', padding=2, relief='flat')
        self.style.configure('Tool.TCombobox', padding=2)
        self.style.configure('Status.TLabel', padding=2)
        
        # Map states for better button feedback
        self.style.map('Tool.TButton',
            background=[('pressed', '!disabled', '#CCE4F7'),
                       ('active', '#E5F1FB')],
            relief=[('pressed', 'sunken'),
                   ('!pressed', 'flat')])
        
        # Create and configure main frame using grid
        self.main_frame = ttk.Frame(self.root, padding="3")
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Change the order: create text widgets before toolbar
        self.create_text_widgets()
        self.create_toolbar()

        # Bind events
        self.bind_shortcuts()
        if sys.platform == 'darwin':
            self.bind_mac_shortcuts()
        
        # Initialize spell checker if available
        if self.SPELL_CHECK_ENABLED:
            try:
                self.spell_checker = enchant.Dict("en_US")
                self.create_spellcheck_menu()
            except:
                self.SPELL_CHECK_ENABLED = False
        
        # Apply theme after all widgets are created
        self.apply_theme(self.current_theme)
        
        # Initialize autosave
        self.autosave_interval = 300
        self.start_autosave()

        self.create_menu()  # Ensure the menu bar is created
        self.bind_cursor_events()
        self.update_all_tags()

        # Add these bindings
        self.text_area.bind('<Return>', self.auto_indent)
        self.text_area.bind('<Key>', self.match_brackets)
        self.text_area.bind('<KeyRelease>', lambda e: self.highlight_syntax())

    def create_text_widgets(self):
        self.text_frame = ttk.Frame(self.main_frame)
        # Create text frame and configure grid
        self.text_frame.grid(row=1, column=0, sticky='nsew')
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.text_frame_inner = ttk.Frame(self.text_frame, padding="2")
        self.text_frame_inner.grid(row=0, column=0, sticky='nsew')
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_frame.grid_columnconfigure(0, weight=1)
        
        # Create line numbers with better sizing
        self.line_numbers = tk.Text(
            self.text_frame_inner,
            width=5,
            padx=4,
            pady=4,
            takefocus=0,
            border=0,
            background=self.current_theme['line_bg'],
            foreground=self.current_theme['line_fg'],
            state='disabled',
            wrap='none'
        )
        self.line_numbers.grid(row=0, column=0, sticky='ns')
        
        # Create text area with better spacing
        self.text_area = tk.Text(
            self.text_frame_inner,
            wrap='word',
            undo=True,
            font=self.text_font,
            padx=8,
            pady=8,
            spacing1=2,  # Add line spacing
            spacing2=2,  # Add paragraph spacing
            spacing3=2   # Add block spacing
        )
        self.text_area.grid(row=0, column=1, sticky='nsew')
        self.text_frame_inner.grid_rowconfigure(0, weight=1)
        self.text_frame_inner.grid_columnconfigure(1, weight=1)
        
        # Create scrollbar with better appearance
        self.scrollbar = ttk.Scrollbar(
            self.text_frame_inner,
            orient='vertical',
            command=self.text_area.yview
        )
        self.scrollbar.grid(row=0, column=2, sticky='ns')
        self.text_area.config(yscrollcommand=self.scrollbar.set)
        
        # Create status bar with better styling
        self.status_bar = ttk.Label(
            self.text_frame,
            text="Ready",
            anchor='w',
            style='Status.TLabel'
        )
        
        # Bind events
        self.text_area.bind('<KeyRelease>', self.on_key_release)
        self.text_area.bind('<Return>', self.auto_indent)
        self.text_area.bind('<Key>', self.match_brackets)
        self.text_area.bind('<MouseWheel>', self.sync_scroll)
        self.text_area.bind('<Button-1>', lambda e: self.sync_scroll())
        self.text_area.bind('<Configure>', lambda e: self.sync_scroll())

        # Add font control update bindings
        self.text_area.bind('<Button-1>', self.update_font_controls)
        self.text_area.bind('<KeyRelease>', self.update_font_controls)
        self.text_area.bind('<<Selection>>', self.update_font_controls)

        # Create status bar and place it at the bottom
        self.status_bar.grid(row=2, column=0, sticky='ew')

    def create_toolbar(self):
        # Create toolbar frame
        self.toolbar = ttk.Frame(self.main_frame, style='Toolbar.TFrame', height=28)
        self.toolbar.grid(row=0, column=0, sticky='ew')
        self.toolbar.grid_propagate(False)  # Maintain fixed height
        
        # File operations group
        file_frame = ttk.Frame(self.toolbar)
        file_frame.pack(side='left', padx=2)
        
        # Compact file operation buttons
        for name, cmd in [("New", self.new_file), 
                         ("Open", self.open_file),
                         ("Save", self.save_file)]:
            btn = ttk.Button(file_frame, text=name, style='Tool.TButton',
                           command=cmd, width=4)
            btn.pack(side='left', padx=1)
        
        ttk.Separator(self.toolbar, orient='vertical').pack(side='left', fill='y', padx=3)
        
        # Font controls
        font_frame = ttk.Frame(self.toolbar)
        font_frame.pack(side='left', padx=2)
        
        # More compact font controls
        common_fonts = ['Consolas', 'Arial', 'Calibri', 'Times New Roman']
        self.font_family_var = tk.StringVar(value=self.current_font_family)
        font_family_menu = ttk.Combobox(
            font_frame,
            textvariable=self.font_family_var,
            values=common_fonts,
            width=10,
            style='Tool.TCombobox',
            state='readonly'
        )
        font_family_menu.pack(side='left', padx=1)
        font_family_menu.bind("<<ComboboxSelected>>", lambda e: self.change_font_family(e, maintain_selection=True))
        
        # More compact size dropdown
        self.font_size_var = tk.IntVar(value=self.current_font_size)
        font_size_menu = ttk.Combobox(
            font_frame,
            textvariable=self.font_size_var,
            values=[8,9,10,11,12,14,16,18,20,24,28,32,36],
            width=3,
            style='Tool.TCombobox',
            state='readonly'
        )
        font_size_menu.pack(side='left', padx=1)
        font_size_menu.bind("<<ComboboxSelected>>", lambda e: self.change_font_size(e, maintain_selection=True))
        
        ttk.Separator(self.toolbar, orient='vertical').pack(side='left', fill='y', padx=3, pady=2)
        
        # Style controls group
        style_frame = ttk.Frame(self.toolbar)
        style_frame.pack(side='left', padx=2)
        
        # Add formatting buttons (more compact)
        self.bold_btn = ttk.Button(style_frame, text="B", style='Tool.TButton', command=self.toggle_bold, width=2)
        self.bold_btn.pack(side='left', padx=1)
        
        self.italic_btn = ttk.Button(style_frame, text="I", style='Tool.TButton', command=self.toggle_italic, width=2)
        self.italic_btn.pack(side='left', padx=1)
        
        self.underline_btn = ttk.Button(style_frame, text="U", style='Tool.TButton', command=self.toggle_underline, width=2)
        self.underline_btn.pack(side='left', padx=1)

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
    
    def change_font_family(self, event=None, maintain_selection=False):
        if maintain_selection:
            try:
                sel_start = self.text_area.index("sel.first")
                sel_end = self.text_area.index("sel.last")
                has_selection = True
            except tk.TclError:
                has_selection = False

        self.current_font_family = self.font_family_var.get()
        if self.text_area.tag_ranges("sel"):
            start = self.text_area.index("sel.first")
            end = self.text_area.index("sel.last")
        else:
            start = "insert"
            end = "insert +1c"

        # Get existing styles at current position
        current_tags = self.text_area.tag_names(start)
        is_bold = 'bold' in current_tags
        is_italic = 'italic' in current_tags
        is_underline = 'underline' in current_tags
            
        # Create and configure font with current styles
        font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)
        if is_bold:
            font.configure(weight='bold')
        if is_italic:
            font.configure(slant='italic')
        if is_underline:
            font.configure(underline=1)
            
        # Apply the combined font configuration
        self.text_area.tag_configure('format', font=font)
        self.text_area.tag_add('format', start, end)

        if maintain_selection and has_selection:
            self.text_area.tag_remove("sel", "1.0", "end")
            self.text_area.tag_add("sel", sel_start, sel_end)

        # ...existing code...
        # After getting current tags, preserve styles while changing font
        active_styles = set()
        for style in ['bold', 'italic', 'underline']:
            if style in current_tags:
                active_styles.add(style)
        
        font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)
        
        # Reapply active styles to new font
        if 'bold' in active_styles:
            font.configure(weight='bold')
        if 'italic' in active_styles:
            font.configure(slant='italic')
        if 'underline' in active_styles:
            font.configure(underline=1)
        
        tag_name = '_'.join(sorted(active_styles)) if active_styles else 'format'
        self.text_area.tag_configure(tag_name, font=font)
        self.text_area.tag_add(tag_name, start, end)
        # ...existing code...

    def change_font_size(self, event=None, maintain_selection=False):
        # Similar changes as change_font_family
        if maintain_selection:
            try:
                sel_start = self.text_area.index("sel.first")
                sel_end = self.text_area.index("sel.last")
                has_selection = True
            except tk.TclError:
                has_selection = False

        self.current_font_size = self.font_size_var.get()
        if self.text_area.tag_ranges("sel"):
            start = self.text_area.index("sel.first")
            end = self.text_area.index("sel.last")
        else:
            start = "insert"
            end = "insert +1c"

        # Get existing styles
        current_tags = self.text_area.tag_names(start)
        is_bold = 'bold' in current_tags
        is_italic = 'italic' in current_tags
        is_underline = 'underline' in current_tags
            
        # Create and configure font with current styles
        font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)
        if is_bold:
            font.configure(weight='bold')
        if is_italic:
            font.configure(slant='italic')
        if is_underline:
            font.configure(underline=1)
            
        # Apply the combined font configuration
        self.text_area.tag_configure('format', font=font)
        self.text_area.tag_add('format', start, end)

        if maintain_selection and has_selection:
            self.text_area.tag_remove("sel", "1.0", "end")
            self.text_area.tag_add("sel", sel_start, sel_end)

        # ...existing code...
        # After getting current tags, preserve styles while changing size
        active_styles = set()
        for style in ['bold', 'italic', 'underline']:
            if style in current_tags:
                active_styles.add(style)
        
        font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)
        
        # Reapply active styles to new font size
        if 'bold' in active_styles:
            font.configure(weight='bold')
        if 'italic' in active_styles:
            font.configure(slant='italic')
        if 'underline' in active_styles:
            font.configure(underline=1)
        
        tag_name = '_'.join(sorted(active_styles)) if active_styles else 'format'
        self.text_area.tag_configure(tag_name, font=font)
        self.text_area.tag_add(tag_name, start, end)
        # ...existing code...

    def toggle_style(self, style):
        try:
            if self.text_area.tag_ranges("sel"):
                start = self.text_area.index("sel.first")
                end = self.text_area.index("sel.last")
            else:
                start = self.text_area.index("insert")
                end = f"{start}+1c"

            # Get current styles at the position
            current_tags = self.text_area.tag_names(start)
            is_style_active = style in current_tags

            # Get current font settings
            current_font = self.text_area.tag_cget('format', 'font') if 'format' in current_tags else None
            if current_font:
                font = tkfont.Font(font=current_font)
            else:
                font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)

            # Update font configuration while preserving other styles
            if style == 'bold':
                font.configure(weight='bold' if not is_style_active else 'normal')
            elif style == 'italic':
                font.configure(slant='italic' if not is_style_active else 'roman')
            elif style == 'underline':
                font.configure(underline=1 if not is_style_active else 0)

            # Create a unique tag name for this combination of styles
            active_styles = set()
            for s in ['bold', 'italic', 'underline']:
                if s in current_tags and s != style:
                    active_styles.add(s)
            if not is_style_active:
                active_styles.add(style)
            
            tag_name = '_'.join(sorted(active_styles)) if active_styles else 'format'

            # Configure and apply the tag
            self.text_area.tag_configure(tag_name, font=font)
            
            # Remove old tags and apply new one
            for old_tag in ['bold', 'italic', 'underline', 'format']:
                self.text_area.tag_remove(old_tag, start, end)
            self.text_area.tag_add(tag_name, start, end)

            # Update the format buttons
            self.update_format_buttons()

            # Handle future typing
            def handle_keypress(event):
                if event.char and not event.char.isspace():
                    current_pos = self.text_area.index("insert")
                    self.text_area.tag_add(tag_name, f"{current_pos}-1c", current_pos)

            self.text_area.bind("<Key>", handle_keypress, add="+")

        except Exception as e:
            print(f"Error in toggle_style: {e}")

    def toggle_bold(self):
        self.toggle_style('bold')

    def toggle_italic(self):
        self.toggle_style('italic')

    def toggle_underline(self):
        self.toggle_style('underline')

    def update_style_tags(self, start, end):
        # Remove existing combined style tags
        tags_to_remove = ['normal', 'bold', 'italic', 'underline',
                          'bold_italic', 'bold_underline', 'italic_underline', 'bold_italic_underline']

        for tag in tags_to_remove:
            self.text_area.tag_remove(tag, start, end)

        # Reapply combined style tags
        index = start
        while self.text_area.compare(index, '<', end):
            current_tags = set(self.text_area.tag_names(index))
            applied_styles = [style for style in ['bold', 'italic', 'underline'] if style in current_tags]
            tag_name = '_'.join(applied_styles) if applied_styles else 'normal'
            self.text_area.tag_add(tag_name, index, f"{index} +1c")
            index = f"{index} +1c"

    def update_all_tags(self):
        # Create font configurations for all style combinations
        base_font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)

        styles = ['bold', 'italic', 'underline']
        combinations = []
        for i in range(1, 8):
            combo = tuple([style for idx, style in enumerate(styles) if i & (1 << idx)])
            combinations.append(combo)
        combinations.append(())

        for combo in combinations:
            tag_name = '_'.join(combo) if combo else 'normal'
            font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)
            if 'bold' in combo:
                font.configure(weight='bold')
            if 'italic' in combo:
                font.configure(slant='italic')
            if 'underline' in combo:
                font.configure(underline=1)
            self.text_area.tag_configure(tag_name, font=font)

    def update_format_buttons(self, event=None):
        try:
            current_tags = self.text_area.tag_names("insert")
            # Configure button appearances based on current style
            self.bold_btn.state(['pressed' if 'bold' in current_tags else '!pressed'])
            self.italic_btn.state(['pressed' if 'italic' in current_tags else '!pressed'])
            self.underline_btn.state(['pressed' if 'underline' in current_tags else '!pressed'])
        except Exception as e:
            print(f"Error in update_format_buttons: {e}")

    def update_font_controls(self, event=None):
        try:
            # Get current position
            if self.text_area.tag_ranges("sel"):
                index = "sel.first"
            else:
                index = "insert"
            
            # Get font at current position
            current_tags = self.text_area.tag_names(index)
            current_font = None
            
            # Try to get font from tags
            for tag in current_tags:
                try:
                    current_font = self.text_area.tag_cget(tag, 'font')
                    if current_font:
                        break
                except:
                    continue
            
            if current_font:
                # Parse font string to get family and size
                font = tkfont.Font(font=current_font)
                family = font.actual('family')
                size = font.actual('size')
                
                # Update font controls without triggering events
                self.font_family_var.set(family)
                self.font_size_var.set(size)
        except Exception as e:
            print(f"Error updating font controls: {e}")

    def bind_cursor_events(self):
        # Bind events to update format buttons
        self.text_area.bind("<KeyRelease>", self.update_format_buttons)
        self.text_area.bind("<ButtonRelease>", self.update_format_buttons)
        self.text_area.bind("<<Selection>>", self.update_format_buttons)

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
        # Update ttk styles for the current theme
        self.style.configure('Toolbar.TFrame', background=theme['menu_bg'])
        self.style.configure('Tool.TButton',
            background=theme['menu_bg'],
            foreground=theme['menu_fg']
        )
        self.style.configure('TCombobox',
            background=theme['menu_bg'],
            foreground=theme['menu_fg'],
            fieldbackground=theme['bg'],
            selectbackground=theme['select_bg'],
            selectforeground=theme['select_fg']
        )
        self.style.configure('TLabel',
            background=theme['menu_bg'],
            foreground=theme['menu_fg']
        )
        self.style.configure('TSeparator',
            background=theme['menu_bg']
        )
        
        # Apply theme to existing widgets
        self.root.configure(bg=theme['bg'])
        self.main_frame.configure(style='Toolbar.TFrame')
        
        # Apply theme to text area
        self.text_area.config(
            bg=theme['bg'],
            fg=theme['fg'],
            insertbackground=theme['cursor'],
            selectbackground=theme['select_bg'],
            selectforeground=theme['select_fg']
        )
        
        # Apply theme to line numbers
        self.line_numbers.config(
            background=theme['line_bg'],
            foreground=theme['line_fg']
        )
        
        # Apply theme to status bar
        self.status_bar.config(
            background=theme['menu_bg'],
            foreground=theme['menu_fg']
        )
        
        # Apply theme to toolbar buttons and menus
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.configure(style='Toolbar.TFrame')
            elif isinstance(widget, ttk.Button):
                widget.configure(style='Tool.TButton')
            elif isinstance(widget, ttk.Combobox):
                widget.configure(style='TCombobox')
            elif isinstance(widget, ttk.Label):
                widget.configure(style='TLabel')
            elif isinstance(widget, ttk.Separator):
                widget.configure(style='TSeparator')
        
        # Update syntax highlighting colors
        self.text_area.tag_config('keyword', foreground=theme['keyword'])
        self.text_area.tag_config('bracket', foreground=theme['bracket'])
        self.text_area.tag_config('misspelled', foreground=theme['misspelled'])
        self.text_area.tag_config('found', foreground=theme['found_fg'], background=theme['found_bg'])

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
        # Get first visible line fraction
        first = self.text_area.yview()[0]
        # Move line_numbers to same fraction
        self.line_numbers.yview_moveto(first)

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
        """Spell check only if enabled"""
        if not self.SPELL_CHECK_ENABLED:
            return
        """Improved spell checking with caching and better word detection"""
        self.text_area.tag_remove('misspelled', '1.0', tk.END)
        
        # Cache for checked words to avoid re-checking
        checked_words = {}
        
        # Get visible text only for performance
        first_visible = self.text_area.index("@0,0")
        last_visible = self.text_area.index(f"@0,{self.text_area.winfo_height()}")
        content = self.text_area.get(first_visible, last_visible)
        
        # Improved word splitting pattern
        import re
        words = re.finditer(r'\b[a-zA-Z]+\b', content)
        
        for match in words:
            word = match.group()
            if word.lower() in checked_words:
                is_correct = checked_words[word.lower()]
            else:
                # Skip checking if word contains numbers or special characters
                if any(not c.isalpha() for c in word):
                    continue
                    
                # Skip short words and probable variable names
                if len(word) <= 1 or (word.lower() != word and word.upper() != word):
                    continue
                    
                is_correct = self.spell_checker.check(word)
                checked_words[word.lower()] = is_correct
            
            if not is_correct:
                start = match.start()
                end = match.end()
                # Convert character offsets to text widget indices
                start_idx = f"{first_visible}+{start}c"
                end_idx = f"{first_visible}+{end}c"
                self.text_area.tag_add('misspelled', start_idx, end_idx)

        # Apply theme-aware misspelled word styling
        self.text_area.tag_config('misspelled', 
                                foreground=self.current_theme['misspelled'],
                                underline=1)

    def create_spellcheck_menu(self):
        self.spellcheck_menu = tk.Menu(self.root, tearoff=0)
        self.spellcheck_menu.add_command(label="Replace with...", command=self.replace_word)
        self.text_area.bind("<Button-3>", self.show_spellcheck_menu)
    
    def show_spellcheck_menu(self, event):
        index = self.text_area.index(f"@{event.x},{event.y}")
        if 'misspelled' in self.text_area.tag_names(index):
            # Get the misspelled word
            word_start = self.text_area.index(f"{index} wordstart")
            word_end = self.text_area.index(f"{index} wordend")
            word = self.text_area.get(word_start, word_end)
            
            # Clear and rebuild the menu
            self.spellcheck_menu.delete(0, tk.END)
            
            # Add suggestions
            suggestions = self.spell_checker.suggest(word)[:5]  # Limit to top 5 suggestions
            for suggestion in suggestions:
                self.spellcheck_menu.add_command(
                    label=suggestion,
                    command=lambda s=suggestion, ws=word_start, we=word_end: self.replace_with_suggestion(s, ws, we)
                )
            
            if suggestions:
                self.spellcheck_menu.add_separator()
            self.spellcheck_menu.add_command(label="Ignore", command=lambda: self.text_area.tag_remove('misspelled', word_start, word_end))
            
            self.spellcheck_menu.tk_popup(event.x_root, event.y_root)

    def replace_with_suggestion(self, suggestion, word_start, word_end):
        self.text_area.delete(word_start, word_end)
        self.text_area.insert(word_start, suggestion)
        self.text_area.tag_remove('misspelled', word_start, f"{word_start}+{len(suggestion)}c")

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