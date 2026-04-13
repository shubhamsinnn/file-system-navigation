# File System Navigator Simulator

**Subject:** Operating Systems (Mini Project)
**Author:** Shubham Singh

A hands-on Operating Systems mini project that simulates how an OS manages and navigates its file system. It provides two fully interactive interfaces: a **Tkinter desktop application** and a **Streamlit web application**, both demonstrating real OS-level file operations.

---

## Table of Contents

1. [Introduction](#introduction)
2. [OS Concepts & Theory](#os-concepts--theory)
3. [How the Code Works](#how-the-code-works)
4. [Features](#features)
5. [Project Structure](#project-structure)
6. [How to Run](#how-to-run)
7. [Deployment on Streamlit Cloud](#deployment-on-streamlit-cloud)
8. [Function Reference](#function-reference)
9. [License](#license)

---

## Introduction

Every operating system provides a **file system** that organizes data into files and directories on storage devices. The file system is responsible for:

- **Storing** data in named files
- **Organizing** files into a hierarchical directory tree
- **Tracking** metadata (size, timestamps, permissions) for every file
- **Providing** system calls (`open`, `read`, `write`, `close`, `unlink`) so user programs can interact with files

This project simulates these interactions using Python. Instead of implementing a file system from scratch, we use Python's `os` module, which directly wraps the operating system's own system calls. Every function in this code maps to a real OS operation.

---

## OS Concepts & Theory

### 1. File System Structure

An OS organizes files in a **hierarchical tree** (also called a directory tree):

```
/  (root)
+-- home/
|   +-- user/
|       +-- Documents/
|       +-- file.txt
+-- etc/
+-- var/
```

- **Root directory** (`/` on Linux, `C:\` on Windows) is the top of the tree.
- **Directories** (folders) are special files that contain pointers to other files and directories.
- **Files** are named collections of data stored on disk.

**In our code:** `os.listdir(path)` reads a directory's contents, just like the OS reads the directory's data block from disk.

### 2. Inodes and File Metadata

Every file on disk has an **inode** (index node) that stores metadata:

| Metadata Field | Description | Python Equivalent |
|---|---|---|
| File size | Number of bytes | `os.path.getsize()` |
| File type | Regular file, directory, link | `os.path.isdir()`, `os.path.isfile()` |
| Timestamps | Created, modified, accessed | `os.stat().st_mtime` |
| Permissions | Read, write, execute flags | `os.stat().st_mode` |
| Data block pointers | Where the file's data lives on disk | (handled internally by OS) |

**In our code:** `os.stat(path)` retrieves the inode information. The `show_metadata()` function reads file size, type, and last-modified time, just as the OS kernel would read the inode structure.

### 3. Path Resolution

When you access `/home/user/file.txt`, the OS performs **path resolution**:

1. Start at the root directory `/`
2. Look up `home` in the root's directory entries
3. Look up `user` in `home`'s directory entries
4. Look up `file.txt` in `user`'s directory entries
5. Return the file's inode

There are two types of paths:
- **Absolute path:** Starts from root (`/home/user/file.txt` or `C:\Users\Shubham\file.txt`)
- **Relative path:** Relative to the current working directory (`./file.txt`)

**In our code:** `os.path.join(current_path, name)` constructs absolute paths. `os.path.dirname(path)` extracts the parent directory (simulates `cd ..`).

### 4. Current Working Directory (CWD)

Every process in an OS has a **current working directory** stored in its Process Control Block (PCB). This determines where relative paths are resolved from.

- `cd /home/user` changes the CWD
- `cd ..` moves to the parent directory
- `pwd` prints the current directory

**In our code:**
- **Tkinter version:** A global variable `current_path` tracks the CWD
- **Streamlit version:** `st.session_state.current_path` persists the CWD across page reruns (since Streamlit re-executes the entire script on every interaction)

### 5. File I/O System Calls

When a program reads or writes a file, it uses **system calls** that transition from user mode to kernel mode:

| System Call | What It Does | Python Equivalent |
|---|---|---|
| `open()` | Opens a file, returns a file descriptor | `open(path, mode)` |
| `read()` | Reads bytes from an open file | `f.read()` |
| `write()` | Writes bytes to an open file | `f.write(content)` |
| `close()` | Closes the file descriptor | Handled by `with` statement |
| `unlink()` | Deletes a file (removes directory entry) | `os.remove(path)` |
| `mkdir()` | Creates a new directory | `os.makedirs(path)` |
| `rename()` | Renames a file (atomic directory entry update) | `os.rename(old, new)` |
| `stat()` | Reads file metadata from the inode | `os.stat(path)` |

**In our code:** Every file operation maps directly to one of these system calls. For example, `open(path, "r")` in Python triggers the OS `open()` system call, which locates the file's inode, checks permissions, and returns a file descriptor.

### 6. File Types and Binary Detection

The OS distinguishes between:
- **Text files:** Contain human-readable characters (`.txt`, `.py`, `.json`)
- **Binary files:** Contain raw bytes (`.pdf`, `.png`, `.exe`)

The OS itself doesn't enforce this distinction at the file system level (files are just bytes), but applications need to know the type to handle them correctly.

**In our code:** `is_binary(path)` reads the first 8KB of a file and checks for **null bytes** (`\x00`). This is the same heuristic used by Git and other tools. Text files never contain null bytes; binary files almost always do.

### 7. Directory Operations

| Operation | OS Concept | Python Code |
|---|---|---|
| List directory | Read directory data block | `os.listdir(path)` |
| Create file | Allocate new inode + directory entry | `open(path, 'w')` |
| Create directory | Allocate new directory inode | `os.makedirs(path)` |
| Rename | Update directory entry (inode unchanged) | `os.rename(old, new)` |
| Delete file | Remove directory entry, free inode | `os.remove(path)` |
| Delete directory | Recursively free all inodes | `shutil.rmtree(path)` |

### 8. Process-File Interaction

When our application opens a file:

1. **User clicks a file** in the GUI
2. Python calls `open(path, "r")` which triggers the OS `open()` system call
3. The OS **resolves the path** to find the file's inode
4. The OS **checks permissions** (can this process read this file?)
5. The OS **allocates a file descriptor** in the process's file descriptor table
6. The OS **reads data blocks** from disk into a kernel buffer
7. The data is **copied to user space** (our Python variable)
8. The file descriptor is **closed** (releasing OS resources)

This entire flow happens every time you click a file in our navigator.

---

## How the Code Works

### Tkinter Version (`app_tkinter.py`)

The desktop app uses a **PanedWindow** layout split into two panels:

- **Left panel (Treeview):** Displays the current directory's contents as a tree with columns for name, type, and size. Each row's `iid` is the full file path, making it easy to retrieve the selected item.

- **Right panel (Text widget):** Displays file content in a read-only text area. When the user clicks "Edit", the widget switches to `state=NORMAL` (writable). "Save" writes content back to disk via `open(path, 'w')`.

- **Toolbar:** Contains buttons for Back, Home, New File, New Folder, Rename, Delete, Open External, Edit, Save, and Cancel.

- **Search bar:** Filters entries in real-time using a `StringVar.trace_add()` callback that re-runs `load_directory()` with the filter applied.

### Streamlit Version (`app_streamlit.py`)

The web app uses `st.columns([1, 2])` to create a two-column layout:

- **Left column:** Shows the current path, Back/Home buttons, a search box, and a list of clickable `st.button()` elements for each directory entry.

- **Right column:** Shows the selected file's content using `st.code()` (with line numbers) in view mode, or `st.text_area()` in edit mode.

- **Sidebar:** Contains expanders for file operations (New File, New Folder, Rename, Delete).

- **Session state:** `st.session_state` stores `current_path`, `selected_file`, and `edit_mode` across reruns, simulating how an OS maintains process state in the PCB.

---

## Features

| Feature | Tkinter | Streamlit |
|---|---|---|
| Browse directories | Treeview with columns | Clickable buttons |
| View file content | Text widget (read-only) | `st.code()` with line numbers |
| Edit and save files | Toggle editable Text widget | `st.text_area()` + Save button |
| Create new files | `simpledialog` input | Sidebar expander |
| Create new folders | `simpledialog` input | Sidebar expander |
| Rename files/folders | `simpledialog` input | Sidebar expander |
| Delete files/folders | Confirmation dialog | Sidebar expander |
| File metadata | Status bar (size, type, date) | `st.caption()` |
| Search/filter | Real-time search box | `st.text_input()` filter |
| Open binary files | System default app via `os.startfile()` | N/A (server-side) |
| Back / Home navigation | Toolbar buttons | Top buttons |

---

## Project Structure

```
file-system-navigation/
    app_tkinter.py      # Desktop GUI (Tkinter + Treeview + file editor)
    app_streamlit.py    # Web app (Streamlit + columns + file editor)
    requirements.txt    # Python dependencies (streamlit)
    README.md           # This file (theory + documentation)
    .gitignore          # Standard Python gitignore
    LICENSE             # MIT License
```

---

## How to Run

### Prerequisites

- Python 3.8 or higher
- `pip` (Python package manager)

### Tkinter Desktop App

No extra installation needed (tkinter is built into Python):

```bash
python app_tkinter.py
```

### Streamlit Web App

Install dependencies first:

```bash
pip install -r requirements.txt
```

Then run:

```bash
streamlit run app_streamlit.py
```

The app opens in your browser at `http://localhost:8501`.

---

## Deployment on Streamlit Cloud

1. Push this repository to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud) and sign in with GitHub
3. Click **New app** and select this repository
4. Set **Main file path** to `app_streamlit.py`
5. Click **Deploy** - Streamlit Cloud installs from `requirements.txt` automatically

> **Note:** On Streamlit Cloud, the app browses the server's Linux container file system (not your local machine). This is expected and still demonstrates all OS concepts.

---

## Function Reference

| Function | File | OS Concept |
|---|---|---|
| `load_directory(path)` | Both | `os.listdir()` reads directory table (like `ls`/`dir`) |
| `open_file(path)` | Both | `open(r)` maps to OS `read()` system call |
| `save_file(path, content)` | Both | `open(w)` maps to OS `write()` system call |
| `show_metadata(path)` | Tkinter | `os.stat()` reads inode metadata (size, timestamps) |
| `get_metadata(path)` | Streamlit | Same as above, returns formatted string |
| `go_back()` | Both | `os.path.dirname()` follows the `..` directory link |
| `go_home()` | Both | `os.path.expanduser("~")` resolves HOME variable |
| `is_binary(path)` | Both | Reads raw bytes to detect binary vs text files |
| `create_file()` | Both | `open(w)` allocates new inode + directory entry |
| `create_folder()` | Both | `os.makedirs()` creates new directory inode |
| `rename_item()` | Both | `os.rename()` atomic update of directory entry |
| `delete_item()` | Both | `os.remove()` / `shutil.rmtree()` frees inode |
| `search_files(query)` | Tkinter | Substring filter on directory entries |
| `open_externally(path)` | Tkinter | `os.startfile()` delegates to OS shell handler |

---

## License

MIT License - see [LICENSE](LICENSE) for details.
