import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import pyperclip
import json
import os
from pathlib import Path

BACKGROUND_COLOR = '#ffffff'  # Clean white background
ACCENT_COLOR = '#007AFF'     # iOS blue
SECONDARY_BG = '#f5f5f7'     # Light gray for frames
TEXT_COLOR = '#1d1d1f'       # Dark gray for text

CONFIG_DIR = Path.home() / '.gooddata_injector'
CONFIG_FILE = CONFIG_DIR / 'config.json'

def copy_to_clipboard(pid, obj_id, button_text):
    try:
        pyperclip.copy(f"[/gdc/md/{pid}/obj/{obj_id}]")
        # Update status label with success message and force update
        status_label.configure(text=f'"{button_text}" has been copied to the clipboard')
        root.update_idletasks()  # Force GUI update
    except Exception as e:
        status_label.configure(text=f'Error copying to clipboard: {str(e)}')
        root.update_idletasks()

def create_button_command(pid_getter, obj_id, name):
    """Create a non-lambda button command with immediate feedback"""
    def command(event=None):  # Allow for both click and keyboard events
        pid = pid_getter()
        copy_to_clipboard(pid, obj_id, name)
    return command

def add_button(frame, pid_combobox):
    pid = pid_combobox.get()
    if not pid:
        messagebox.showwarning("Warning", "Please select or add a PID first")
        return
    
    dialog = tk.Toplevel()
    dialog.title("Add New Item")
    dialog.geometry("300x180")
    dialog.configure(bg=BACKGROUND_COLOR)
    dialog.transient(frame)
    dialog.grab_set()
    
    dialog.geometry(f"+{frame.winfo_rootx() + 50}+{frame.winfo_rooty() + 50}")
    
    name_label = ttk.Label(dialog, text="Name:", background=BACKGROUND_COLOR)
    name_label.pack(pady=(10,0))
    name_entry = ttk.Entry(dialog, width=30, style='Modern.TEntry')
    name_entry.pack(pady=(0,10))
    
    id_label = ttk.Label(dialog, text="ID:", background=BACKGROUND_COLOR)
    id_label.pack()
    id_entry = ttk.Entry(dialog, width=30, style='Modern.TEntry')
    id_entry.pack(pady=(0,10))
    
    def submit():
        name = name_entry.get()
        obj_id = id_entry.get()
        if name and obj_id:
            btn = ttk.Button(frame, text=name, style='Modern.TButton')
            cmd = create_button_command(pid_combobox.get, obj_id, name)
            btn.configure(command=cmd)
            btn.bind('<Return>', cmd)
            btn.bind('<space>', cmd)
            btn.obj_id = obj_id
            btn.pack(pady=5, padx=5, fill='x')
            
            btn.bind('<Button-3>', show_button_menu)  # Right-click on Windows/Linux
            btn.bind('<Control-1>', show_button_menu)  # Control+click on Mac
            
            btn.bind('<Enter>', lambda e, b=btn: b.configure(style='ModernHover.TButton'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(style='Modern.TButton'))
            save_app_state()  # Save changes
        dialog.destroy()

    button_frame = ttk.Frame(dialog, style='Modern.TFrame')
    button_frame.pack(pady=10, fill='x', padx=10)
    
    cancel_btn = ttk.Button(button_frame, text="Cancel", style='Modern.TButton', 
                           command=dialog.destroy)
    save_btn = ttk.Button(button_frame, text="Save", style='Modern.TButton', 
                         command=submit)
    
    cancel_btn.pack(side='left', padx=(0,5), expand=True, fill='x')
    save_btn.pack(side='right', padx=(5,0), expand=True, fill='x')

def save_app_state():
    """Save the current state of the app to a JSON file"""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True)
    
    app_state = {
        'current_pid': pid_combobox.get(),
        'saved_pids': list(pid_combobox['values']),
        'metrics': [],
        'attributes': [],
        'dates': []
    }
    
    # Helper function to get button data from a frame
    def get_frame_buttons(frame):
        buttons = []
        for widget in frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget('text') != '+':
                try:
                    buttons.append({
                        'name': widget.cget('text'),
                        'id': widget.obj_id
                    })
                except AttributeError:
                    continue
        return buttons
    
    app_state['metrics'] = get_frame_buttons(metrics_frame)
    app_state['attributes'] = get_frame_buttons(attributes_frame)
    app_state['dates'] = get_frame_buttons(dates_frame)
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(app_state, f, indent=2)

def load_app_state():
    """Load the saved state of the app from JSON file"""
    if not CONFIG_FILE.exists():
        return
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            app_state = json.load(f)
        
        # Restore PIDs
        if 'saved_pids' in app_state:
            pid_combobox['values'] = tuple(app_state['saved_pids'])
        if 'current_pid' in app_state:
            pid_combobox.set(app_state['current_pid'])
        
        # Helper function to restore buttons to a frame
        def restore_frame_buttons(frame, buttons):
            for btn_data in buttons:
                btn = ttk.Button(frame, text=btn_data['name'], style='Modern.TButton')
                btn.obj_id = btn_data['id']
                btn.configure(command=create_button_command(pid_combobox.get, btn_data['id'], btn_data['name']))
                btn.pack(pady=5, padx=5, fill='x')
                
                btn.bind('<Button-3>', show_button_menu)  # Right-click on Windows/Linux
                btn.bind('<Control-1>', show_button_menu)  # Control+click on Mac
                
                btn.bind('<Enter>', lambda e, btn=btn: btn.configure(style='ModernHover.TButton'))
                btn.bind('<Leave>', lambda e, btn=btn: btn.configure(style='Modern.TButton'))
        
        # Restore buttons
        restore_frame_buttons(metrics_frame, app_state.get('metrics', []))
        restore_frame_buttons(attributes_frame, app_state.get('attributes', []))
        restore_frame_buttons(dates_frame, app_state.get('dates', []))
        
    except Exception as e:
        print(f"Error loading app state: {e}")

# Modify the root window to save state on closing
def on_closing():
    save_app_state()
    root.destroy()

def add_new_pid():
    """Add a new PID to the combobox"""
    new_pid = simpledialog.askstring("Add PID", "Enter new PID:")
    if new_pid:
        current_values = list(pid_combobox['values'])
        if new_pid not in current_values:
            current_values.append(new_pid)
            pid_combobox['values'] = tuple(current_values)
        pid_combobox.set(new_pid)

class AutocompleteText(tk.Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.suggestions = []
        self.current_suggestion = None
        self.references = []  # List to store references and their positions
        
        # Configure tags for visual styling
        self.tag_configure('reference', foreground='#28a745', font=('Consolas', 11, 'bold'))
        self.tag_configure('metric_reference', foreground='#28a745', font=('Consolas', 11, 'bold'))
        self.tag_configure('other_reference', foreground='#9932CC', font=('Consolas', 11, 'bold'))  # Purple color
        
        # Create floating listbox for suggestions
        self.suggestion_box = tk.Listbox(
            root,
            font=('Consolas', 11),
            selectmode=tk.SINGLE,
            activestyle='none',
            bg='white',
            fg=TEXT_COLOR,
            relief='solid',
            borderwidth=1
        )
        
        # Bind events
        self.bind('<KeyRelease>', self.check_autocomplete)
        self.bind('<Tab>', self.apply_selection)
        self.bind('<Up>', self.move_selection)
        self.bind('<Down>', self.move_selection)
        self.bind('<Return>', self.apply_selection)
        self.bind('<FocusOut>', lambda e: self.after(100, self.hide_suggestions))
        
    def get_all_button_names(self):
        """Get all button names from the frames"""
        names = []
        for frame in [metrics_frame, attributes_frame, dates_frame]:
            for widget in frame.winfo_children():
                if isinstance(widget, ttk.Button) and widget.cget('text') != '+':
                    names.append({
                        'text': widget.cget('text'),
                        'id': widget.obj_id
                    })
        return names
    
    def get_current_word(self):
        """Get the word currently being typed"""
        current_line = self.get('insert linestart', 'insert')
        if not current_line:
            return ''
        words = current_line.split()
        return words[-1] if words else ''
    
    def show_suggestions(self, suggestions):
        """Display suggestion listbox below current cursor position"""
        if not suggestions:
            self.hide_suggestions()
            return
        
        # Get cursor position on screen
        bbox = self.bbox('insert')
        if not bbox:
            return
        
        x, y, _, h = bbox
        x = self.winfo_rootx() + x
        y = self.winfo_rooty() + y + h + 2
        
        # Update and show suggestion box
        self.suggestion_box.delete(0, tk.END)
        for item in suggestions:
            self.suggestion_box.insert(tk.END, item['text'])
        
        # Size and position the listbox
        height = min(len(suggestions), 6)  # Show max 6 items
        self.suggestion_box.configure(height=height)
        self.suggestion_box.place(x=x, y=y, width=300)
        
        if not self.suggestion_box.curselection():
            self.suggestion_box.selection_set(0)
    
    def hide_suggestions(self):
        """Hide the suggestion listbox"""
        self.suggestion_box.place_forget()
    
    def move_selection(self, event):
        """Handle up/down arrow key navigation"""
        if not self.suggestion_box.winfo_viewable():
            return
        
        current = self.suggestion_box.curselection()
        if not current:
            self.suggestion_box.selection_set(0)
            return 'break'
        
        current = current[0]
        if event.keysym == 'Up' and current > 0:
            self.suggestion_box.selection_clear(current)
            self.suggestion_box.selection_set(current - 1)
        elif event.keysym == 'Down' and current < self.suggestion_box.size() - 1:
            self.suggestion_box.selection_clear(current)
            self.suggestion_box.selection_set(current + 1)
        return 'break'
    
    def handle_selection(self, event):
        """Handle listbox selection"""
        if self.suggestion_box.curselection():
            self.apply_selection(None)
    
    def check_autocomplete(self, event):
        """Check for autocomplete suggestions"""
        if event.keysym in ('Up', 'Down', 'Return', 'Tab'):
            return
        
        current_word = self.get_current_word()
        if len(current_word) < 2:
            self.hide_suggestions()
            return
        
        # Get matching suggestions
        all_names = self.get_all_button_names()
        self.suggestions = [item for item in all_names 
                          if item['text'].lower().startswith(current_word.lower())]
        
        # Show or hide suggestions
        if self.suggestions:
            self.show_suggestions(self.suggestions)
        else:
            self.hide_suggestions()
    
    def get_display_text(self, name):
        """Returns the display text for the editor"""
        return name
    
    def get_reference_text(self, pid, obj_id):
        """Returns the actual reference text for copying"""
        return f"[/gdc/md/{pid}/obj/{obj_id}]"
    
    def apply_selection(self, event):
        """Apply the selected suggestion"""
        if not self.suggestion_box.winfo_viewable():
            return
        
        selection = self.suggestion_box.curselection()
        if not selection:
            return 'break'
        
        selected_item = self.suggestions[selection[0]]
        
        # Determine which frame the button belongs to
        button_frame = None
        for widget in metrics_frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget('text') == selected_item['text']:
                button_frame = 'metrics'
                break
        if not button_frame:
            for frame in [attributes_frame, dates_frame]:
                for widget in frame.winfo_children():
                    if isinstance(widget, ttk.Button) and widget.cget('text') == selected_item['text']:
                        button_frame = 'other'
                        break
                if button_frame:
                    break
        
        # Get the current line up to the cursor
        current_line = self.get('insert linestart', 'insert')
        words = current_line.split()
        if not words:
            return 'break'
        
        # Calculate positions
        current_word = words[-1]
        start_pos = f"insert-{len(current_word)}c"
        
        # Replace the current word with the styled display text
        self.delete(start_pos, 'insert')
        display_text = self.get_display_text(selected_item['text'])
        
        # Store reference information
        start_index = self.index('insert')
        self.insert('insert', display_text)
        end_index = self.index('insert')
        
        # Add to references list
        reference = self.get_reference_text(pid_combobox.get(), selected_item['id'])
        self.references.append({
            'display': display_text,
            'reference': reference,
            'start': start_index,
            'end': end_index
        })
        
        # Apply appropriate tag based on the source frame
        tag_name = 'metric_reference' if button_frame == 'metrics' else 'other_reference'
        self.tag_add(tag_name, start_index, end_index)
        
        # Hide suggestions
        self.hide_suggestions()
        return 'break'

def edit_button(button):
    """Edit an existing button's name and ID"""
    dialog = tk.Toplevel()
    dialog.title("Edit Item")
    dialog.geometry("300x180")
    dialog.configure(bg=BACKGROUND_COLOR)
    dialog.transient(button.winfo_toplevel())
    dialog.grab_set()
    
    # Position dialog near the button
    dialog.geometry(f"+{button.winfo_rootx() + 50}+{button.winfo_rooty() + 50}")
    
    # Current values
    current_name = button.cget('text')
    current_id = button.obj_id
    
    name_label = ttk.Label(dialog, text="Name:", background=BACKGROUND_COLOR)
    name_label.pack(pady=(10,0))
    name_entry = ttk.Entry(dialog, width=30, style='Modern.TEntry')
    name_entry.insert(0, current_name)
    name_entry.pack(pady=(0,10))
    
    id_label = ttk.Label(dialog, text="ID:", background=BACKGROUND_COLOR)
    id_label.pack()
    id_entry = ttk.Entry(dialog, width=30, style='Modern.TEntry')
    id_entry.insert(0, current_id)
    id_entry.pack(pady=(0,10))
    
    def submit():
        new_name = name_entry.get()
        new_id = id_entry.get()
        if new_name and new_id:
            button.configure(text=new_name)
            button.obj_id = new_id
            # Update the button command with new values
            cmd = create_button_command(pid_combobox.get, new_id, new_name)
            button.configure(command=cmd)
            button.bind('<Return>', cmd)
            button.bind('<space>', cmd)
            
            # Reapply hover bindings
            button.bind('<Enter>', lambda e, b=button: b.configure(style='ModernHover.TButton'))
            button.bind('<Leave>', lambda e, b=button: b.configure(style='Modern.TButton'))
            
            save_app_state()  # Save changes
        dialog.destroy()
    
    button_frame = ttk.Frame(dialog, style='Modern.TFrame')
    button_frame.pack(pady=10, fill='x', padx=10)
    
    cancel_btn = ttk.Button(button_frame, text="Cancel", style='Modern.TButton', 
                           command=dialog.destroy)
    save_btn = ttk.Button(button_frame, text="Save", style='Modern.TButton', 
                         command=submit)
    
    cancel_btn.pack(side='left', padx=(0,5), expand=True, fill='x')
    save_btn.pack(side='right', padx=(5,0), expand=True, fill='x')

def delete_button(button):
    """Delete a button after confirmation"""
    if messagebox.askyesno("Confirm Delete", 
                          f"Are you sure you want to delete '{button.cget('text')}'?"):
        button.destroy()
        save_app_state()  # Save changes

def show_button_menu(event):
    """Show context menu for button"""
    button = event.widget
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Edit", 
                    command=lambda: edit_button(button))
    menu.add_command(label="Delete", 
                    command=lambda: delete_button(button))
    menu.post(event.x_root, event.y_root)

root = tk.Tk()
root.title("GoodData Injector")

style = ttk.Style(root)
style.theme_use('clam')

# Configure modern styling
style.configure('.', 
    background=BACKGROUND_COLOR,
    foreground=TEXT_COLOR,
    fieldbackground=BACKGROUND_COLOR)

style.configure('Modern.TButton',
    background=ACCENT_COLOR,
    foreground='white',
    padding=(10, 5),
    relief='flat',
    borderwidth=0)
style.map('Modern.TButton',
    background=[('active', '#005ECE')])  # Darker blue when clicked

style.configure('Add.TButton',
    background=ACCENT_COLOR,
    foreground='white',
    padding=(15, 8),
    font=('SF Pro Display', 14, 'bold'))  # Modern font

style.configure('Modern.TEntry',
    padding=(10, 5),
    fieldbackground='white',
    bordercolor=ACCENT_COLOR)

style.configure('Modern.TLabelframe',
    background=SECONDARY_BG,
    padding=15)
style.configure('Modern.TLabelframe.Label',
    background=SECONDARY_BG,
    foreground=TEXT_COLOR,
    font=('SF Pro Display', 12, 'bold'))

style.configure('Modern.TCombobox',
    background=BACKGROUND_COLOR,
    foreground=TEXT_COLOR,
    fieldbackground='white',
    arrowcolor=ACCENT_COLOR)

style.configure('ModernHover.TButton',
    background='#005ECE',  # Darker blue for hover
    foreground='white',
    padding=(10, 5),
    relief='flat',
    borderwidth=0)

style.map('Modern.TButton',
    background=[('pressed', '#004BB1'),  # Even darker blue when pressed
                ('active', '#005ECE')],
    relief=[('pressed', 'sunken')])

root.configure(bg=BACKGROUND_COLOR)
main_frame = ttk.Frame(root, padding=20)
main_frame.grid(sticky='nsew')
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

pid_frame = ttk.Frame(main_frame)
pid_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
pid_frame.columnconfigure(1, weight=1)

pid_label = ttk.Label(pid_frame, text="PID:", font=('SF Pro Display', 12))
pid_label.grid(row=0, column=0, sticky="w")

pid_combobox = ttk.Combobox(pid_frame, style='Modern.TCombobox', width=30, state='readonly')
pid_combobox.grid(row=0, column=1, sticky="ew", padx=(5, 5))

add_pid_button = ttk.Button(pid_frame, text="+", style='Add.TButton', 
                           command=add_new_pid, width=3)
add_pid_button.grid(row=0, column=2, sticky="e")

metrics_frame = ttk.LabelFrame(main_frame, text="Metrics", style='Modern.TLabelframe')
attributes_frame = ttk.LabelFrame(main_frame, text="Attributes", style='Modern.TLabelframe')
dates_frame = ttk.LabelFrame(main_frame, text="Dates", style='Modern.TLabelframe')
metrics_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
attributes_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
dates_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")

add_metric_btn = ttk.Button(metrics_frame, text="+", style='Add.TButton', command=lambda: add_button(metrics_frame, pid_combobox))
add_metric_btn.pack(pady=5, fill='x')
add_attribute_btn = ttk.Button(attributes_frame, text="+", style='Add.TButton', command=lambda: add_button(attributes_frame, pid_combobox))
add_attribute_btn.pack(pady=5, fill='x')
add_date_btn = ttk.Button(dates_frame, text="+", style='Add.TButton', command=lambda: add_button(dates_frame, pid_combobox))
add_date_btn.pack(pady=5, fill='x')

# Add this after the frames are created but before root.mainloop()
status_label = ttk.Label(main_frame, text="", font=('SF Pro Display', 10), foreground=TEXT_COLOR)
status_label.grid(row=2, column=0, columnspan=3, pady=(10,0), sticky="ew")

# Add these lines before root.mainloop()
root.protocol("WM_DELETE_WINDOW", on_closing)
load_app_state()

# Add these lines before root.mainloop() but after creating the main UI elements
code_frame = ttk.Frame(main_frame)
code_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
code_frame.columnconfigure(0, weight=1)

code_text = AutocompleteText(
    code_frame,
    height=10,
    wrap='word',
    font=('Consolas', 11),
    bg='white',
    fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR,
    relief='solid',
    borderwidth=1
)
code_text.grid(row=0, column=0, sticky="ew")

# Add scrollbar
code_scrollbar = ttk.Scrollbar(code_frame, orient='vertical', command=code_text.yview)
code_scrollbar.grid(row=0, column=1, sticky='ns')
code_text.configure(yscrollcommand=code_scrollbar.set)

def copy_code_content():
    """Copy the contents of the code text box to clipboard, replacing display text with references"""
    # Get all text
    final_text = code_text.get("1.0", tk.END).strip()
    if not final_text:
        status_label.configure(text="No code to copy")
        root.update_idletasks()
        return
    
    # Replace all references
    if hasattr(code_text, 'references'):
        # Process references in reverse order to avoid position issues
        for ref in reversed(code_text.references):
            final_text = final_text.replace(ref['display'], ref['reference'])
    
    pyperclip.copy(final_text)
    status_label.configure(text="Code copied to clipboard!")
    root.update_idletasks()

copy_button = ttk.Button(
    code_frame,
    text="Copy Code",
    style='Modern.TButton',
    command=copy_code_content
)
copy_button.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky="ew")

root.mainloop()
