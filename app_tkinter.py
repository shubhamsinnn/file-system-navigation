"""
File System Navigator Simulator - Tkinter Desktop App (Intermediate)
Subject: Operating Systems (Mini Project)
Demonstrates: directory trees, file I/O, metadata (inodes), path resolution,
              file creation/deletion, renaming - all core OS file-system operations.
"""

import os
import os.path
import shutil
import datetime
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Supported text extensions - OS identifies file types via extensions or magic bytes
SUPPORTED_EXT = {".txt", ".py", ".md", ".json", ".csv", ".log", ".html", ".css",
                 ".js", ".xml", ".ini", ".cfg", ".yaml", ".yml", ".toml"}

current_path = os.path.expanduser("~")  # CWD - OS tracks this per process in the PCB


# -- Directory loading ---------------------------------------------------

def load_directory(path):
    """Populate the Treeview with contents of the given directory."""
    global current_path
    current_path = path
    path_var.set(current_path)  # Update address bar - mirrors a file explorer's path bar
    for item in tree.get_children():
        tree.delete(item)  # Clear tree - OS re-reads the directory table on each ls/dir
    try:
        # os.listdir() reads the directory block from disk - like reading a directory inode
        entries = sorted(os.listdir(path), key=str.lower)
        query = search_var.get().lower()  # Live search filter
        for name in entries:
            if query and query not in name.lower():
                continue
            full = os.path.join(path, name)
            try:
                # os.path.isdir() inspects file metadata to determine entry type
                kind = "folder" if os.path.isdir(full) else "file"
                size = "" if kind == "folder" else f"{os.path.getsize(full):,} B"
                tree.insert("", tk.END, iid=full, text=name, values=(kind, size))
            except (PermissionError, OSError):
                tree.insert("", tk.END, iid=full, text=name, values=("error", "---"))
    except PermissionError:
        messagebox.showerror("Access Denied", f"Cannot read:\n{path}")
    status_var.set(f"  {path}")

def go_back():
    """Navigate to parent directory - simulates 'cd ..' (following the '..' link)."""
    parent = os.path.dirname(current_path)  # os.path.dirname strips last path component
    if parent != current_path:
        load_directory(parent)

def go_home():
    """Jump to user home - os.path.expanduser('~') resolves the HOME env variable."""
    load_directory(os.path.expanduser("~"))


# -- File viewing --------------------------------------------------------

def is_binary(path, check_bytes=8192):
    """Check if a file is binary by looking for null bytes - OS reads raw bytes from disk."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(check_bytes)
        return b"\x00" in chunk  # Null bytes indicate binary data (PDF, images, exe)
    except Exception:
        return True

def open_externally(path):
    """Open a file with the system default app - OS finds the registered handler."""
    try:
        os.startfile(path)  # Windows: shell delegates to the file-type handler
    except AttributeError:
        subprocess.Popen(["xdg-open", path])  # Linux/Mac fallback
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file:\n{e}")

def open_file(path):
    """Read a file from disk and display its content in the viewer panel."""
    text_widget.config(state=tk.NORMAL)
    text_widget.delete("1.0", tk.END)  # Clear viewer before loading new content

    if is_binary(path):
        ext = os.path.splitext(path)[1].lower()
        text_widget.insert(tk.END, f"Binary file detected ({ext})\n\n")
        text_widget.insert(tk.END, "This file cannot be displayed as text.\n")
        text_widget.insert(tk.END, "Click [Open External] in the toolbar to open it\n")
        text_widget.insert(tk.END, "with your system default application (e.g. PDF reader).")
        text_widget.config(state=tk.DISABLED)
        show_metadata(path)
        return

    try:
        # open() is a system call abstraction - OS loads file from disk into user-space memory
        # errors='replace' handles any encoding issues so the file always opens
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        text_widget.insert(tk.END, content)
    except PermissionError:
        text_widget.insert(tk.END, "[Permission Denied] Cannot read this file.")
    except Exception as e:
        text_widget.insert(tk.END, f"[Error] {e}")
    text_widget.config(state=tk.DISABLED)
    show_metadata(path)

def show_metadata(path):
    """Display file metadata - OS stores this in the inode (Unix) or MFT entry (Windows)."""
    try:
        # os.stat() retrieves file metadata from the OS - similar to inode access in Unix
        info = os.stat(path)
        size_kb = info.st_size / 1024
        ext = os.path.splitext(path)[1] or "(none)"
        # st_mtime is the last-modified timestamp - OS updates this on every write() call
        mtime = datetime.datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M")
        status_var.set(f"  {os.path.basename(path)}  |  {size_kb:.1f} KB  |  Type: {ext}  |  Modified: {mtime}")
    except OSError:
        status_var.set("  (metadata unavailable)")


# -- File editing --------------------------------------------------------

selected_file = None  # Tracks which file is currently open in the viewer

def start_edit():
    """Unlock the text panel so the user can modify the file content."""
    if not selected_file:
        messagebox.showinfo("No File", "Open a file first before editing.")
        return
    if is_binary(selected_file):
        messagebox.showinfo("Binary File", "This is a binary file.\nUse [Open External] to view it.")
        return
    text_widget.config(state=tk.NORMAL)
    status_var.set("  EDITING: " + os.path.basename(selected_file))

def save_file(path, content):
    """Write content back to disk - open(w) triggers an OS write() system call."""
    # open(path, 'w') truncates the file then writes - OS updates the file's data blocks
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def do_save():
    """Save handler - confirms with user, writes to disk, and re-locks the panel."""
    if not selected_file:
        return
    if not messagebox.askyesno("Save File", f"Save changes to\n{os.path.basename(selected_file)}?"):
        return
    try:
        content = text_widget.get("1.0", "end-1c")
        save_file(selected_file, content)
        text_widget.config(state=tk.DISABLED)
        status_var.set("  Saved: " + os.path.basename(selected_file))
    except Exception as e:
        messagebox.showerror("Save Error", str(e))

def cancel_edit():
    """Discard edits - reload original content from disk and lock the panel."""
    if selected_file:
        open_file(selected_file)


# -- File & folder operations --------------------------------------------

def create_file():
    """Create a new empty file - open(w) allocates a new inode and directory entry."""
    name = simpledialog.askstring("New File", "Enter file name (with extension):")
    if not name:
        return
    path = os.path.join(current_path, name)
    if os.path.exists(path):
        messagebox.showerror("Exists", "A file with this name already exists.")
        return
    try:
        # open(path, 'w') is a create system call - OS allocates disk blocks and an inode
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        load_directory(current_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def create_folder():
    """Create a new directory - os.makedirs allocates a new directory inode on disk."""
    name = simpledialog.askstring("New Folder", "Enter folder name:")
    if not name:
        return
    path = os.path.join(current_path, name)
    try:
        # os.makedirs() creates directory entries - OS updates the parent's data block
        os.makedirs(path, exist_ok=False)
        load_directory(current_path)
    except FileExistsError:
        messagebox.showerror("Exists", "A folder with this name already exists.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def get_selected_path():
    """Return the full path of the currently selected Treeview item."""
    sel = tree.selection()
    return sel[0] if sel else None

def rename_item():
    """Rename a file or folder - os.rename() is an atomic OS operation on the dir entry."""
    path = get_selected_path()
    if not path:
        messagebox.showinfo("No Selection", "Select an item first.")
        return
    old_name = os.path.basename(path)
    new_name = simpledialog.askstring("Rename", f"Rename '{old_name}' to:", initialvalue=old_name)
    if not new_name or new_name == old_name:
        return
    try:
        # os.rename() updates the filename in the directory entry - inode stays the same
        os.rename(path, os.path.join(os.path.dirname(path), new_name))
        load_directory(current_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def delete_item():
    """Delete a file or folder - os.remove / shutil.rmtree free disk blocks and inode."""
    path = get_selected_path()
    if not path:
        messagebox.showinfo("No Selection", "Select an item first.")
        return
    name = os.path.basename(path)
    if not messagebox.askyesno("Delete", f"Permanently delete '{name}'?"):
        return
    try:
        if os.path.isdir(path):
            # shutil.rmtree() recursively removes directory - simulates rm -rf at OS level
            shutil.rmtree(path)
        else:
            # os.remove() deletes the directory entry and frees the inode
            os.remove(path)
        load_directory(current_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))


# -- Search --------------------------------------------------------------

def search_files(query=None):
    """Filter visible items by name - simple substring match on directory entries."""
    load_directory(current_path)


# -- Tree event handlers --------------------------------------------------

def on_tree_select(event):
    """Handle single-click - if file, show content; if folder, just select it."""
    global selected_file
    path = get_selected_path()
    if not path or not os.path.exists(path):
        return
    if os.path.isfile(path):
        selected_file = path
        open_file(path)
    else:
        selected_file = None

def on_tree_double_click(event):
    """Handle double-click - if folder, navigate into it."""
    path = get_selected_path()
    if path and os.path.isdir(path):
        load_directory(path)


# ========================================================================
# GUI CONSTRUCTION
# ========================================================================

root = tk.Tk()
root.title("File System Navigator - OS Mini Project")
root.geometry("960x600")
root.minsize(700, 400)

# -- Top bar: path + search --
top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=6, pady=(6, 2))

path_var = tk.StringVar(value=current_path)
tk.Label(top_frame, textvariable=path_var, anchor="w", font=("Consolas", 10),
         bg="#1e1e1e", fg="#dcdcdc", padx=8, pady=4).pack(side="left", fill="x", expand=True)

search_var = tk.StringVar()
search_var.trace_add("write", lambda *_: search_files())
tk.Entry(top_frame, textvariable=search_var, width=22, font=("Arial", 10)).pack(side="right", padx=(6, 0))
tk.Label(top_frame, text="Search:", font=("Arial", 10)).pack(side="right")

# -- Toolbar --
toolbar = tk.Frame(root)
toolbar.pack(fill="x", padx=6, pady=2)

btn_cfg = dict(font=("Arial", 9), padx=6, pady=2)
tk.Button(toolbar, text="Back", command=go_back, **btn_cfg).pack(side="left", padx=2)
tk.Button(toolbar, text="Home", command=go_home, **btn_cfg).pack(side="left", padx=2)
ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
tk.Button(toolbar, text="New File", command=create_file, **btn_cfg).pack(side="left", padx=2)
tk.Button(toolbar, text="New Folder", command=create_folder, **btn_cfg).pack(side="left", padx=2)
tk.Button(toolbar, text="Rename", command=rename_item, **btn_cfg).pack(side="left", padx=2)
tk.Button(toolbar, text="Delete", command=delete_item, **btn_cfg).pack(side="left", padx=2)

def do_open_external():
    if selected_file:
        open_externally(selected_file)
    else:
        messagebox.showinfo("No File", "Select a file first.")

tk.Button(toolbar, text="Open External", command=do_open_external, **btn_cfg).pack(side="left", padx=2)
ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
tk.Button(toolbar, text="Edit", command=start_edit, **btn_cfg).pack(side="left", padx=2)
tk.Button(toolbar, text="Save", command=do_save, **btn_cfg).pack(side="left", padx=2)
tk.Button(toolbar, text="Cancel", command=cancel_edit, **btn_cfg).pack(side="left", padx=2)

# -- Main paned area: tree (left) + viewer (right) --
pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=5)
pane.pack(fill="both", expand=True, padx=6, pady=2)

# Left: Treeview for folder/file listing
tree_frame = tk.Frame(pane)
tree_scroll = tk.Scrollbar(tree_frame)
tree_scroll.pack(side="right", fill="y")

tree = ttk.Treeview(tree_frame, columns=("type", "size"), show="tree headings",
                    yscrollcommand=tree_scroll.set)
tree.heading("#0", text="Name", anchor="w")
tree.heading("type", text="Type", anchor="w")
tree.heading("size", text="Size", anchor="e")
tree.column("#0", width=200, minwidth=120)
tree.column("type", width=60, minwidth=50)
tree.column("size", width=90, minwidth=60, anchor="e")
tree.pack(fill="both", expand=True)
tree_scroll.config(command=tree.yview)

tree.bind("<<TreeviewSelect>>", on_tree_select)
tree.bind("<Double-1>", on_tree_double_click)
pane.add(tree_frame, width=340)

# Right: Text widget for file content viewing/editing
text_frame = tk.Frame(pane)
text_scroll = tk.Scrollbar(text_frame)
text_scroll.pack(side="right", fill="y")

text_widget = tk.Text(text_frame, wrap="none", font=("Consolas", 10), state=tk.DISABLED,
                      yscrollcommand=text_scroll.set, bg="#fafafa")
text_widget.pack(fill="both", expand=True)
text_scroll.config(command=text_widget.yview)
pane.add(text_frame)

# -- Status bar --
status_var = tk.StringVar(value="  Ready")
tk.Label(root, textvariable=status_var, anchor="w", font=("Consolas", 9),
         bg="#2d2d2d", fg="#cccccc", padx=6, pady=3).pack(fill="x", side="bottom")

# -- Initial load and start --
load_directory(current_path)
root.mainloop()
