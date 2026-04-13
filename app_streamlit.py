"""
File System Navigator Simulator - Streamlit Web App (Intermediate)
Subject: Operating Systems (Mini Project)
Demonstrates: directory listing, file I/O, metadata, path resolution,
              file creation/deletion/renaming via OS system calls.
Uses st.session_state to persist CWD across reruns (like a process's PCB).
"""

import os
import os.path
import shutil
import datetime
import streamlit as st

# File types we can display as text in the browser
SUPPORTED_EXT = {".txt", ".py", ".md", ".json", ".csv", ".log", ".html", ".css",
                 ".js", ".xml", ".ini", ".cfg", ".yaml", ".yml", ".toml"}

st.set_page_config(page_title="File System Navigator", layout="wide")
st.title("File System Navigator")
st.caption("OS Mini Project - file I/O, directory trees, metadata, path resolution")

# -- Session state init (like OS keeping CWD in the process control block) --
if "current_path" not in st.session_state:
    st.session_state.current_path = os.path.expanduser("~")
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def load_directory(path):
    """Read directory entries and return sorted list of (name, is_dir) tuples."""
    try:
        # os.listdir() reads the directory table from disk
        entries = sorted(os.listdir(path), key=str.lower)
        result = []
        for name in entries:
            full = os.path.join(path, name)
            try:
                result.append((name, os.path.isdir(full)))
            except OSError:
                result.append((name, False))
        return result
    except PermissionError:
        st.error("Access denied - cannot read this directory.")
        return []

def is_binary(path, check_bytes=8192):
    """Check if a file is binary by looking for null bytes."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(check_bytes)
        return b"\x00" in chunk
    except Exception:
        return True

def open_file(path):
    """Read file content from disk. Returns (content, error_message)."""
    if is_binary(path):
        ext = os.path.splitext(path)[1].lower()
        return None, f"Binary file ({ext}) - cannot display as text."
    try:
        # open() is a system call abstraction - OS reads data blocks into user memory
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), None
    except PermissionError:
        return None, "Permission denied."
    except Exception as e:
        return None, str(e)

def save_file(path, content):
    """Write content to disk - OS truncates then writes data blocks."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def go_back():
    """Navigate to parent directory - os.path.dirname simulates 'cd ..'."""
    parent = os.path.dirname(st.session_state.current_path)
    if parent != st.session_state.current_path:
        st.session_state.current_path = parent
        st.session_state.selected_file = None
        st.session_state.edit_mode = False

def go_home():
    """Jump to home directory - resolves the HOME environment variable."""
    st.session_state.current_path = os.path.expanduser("~")
    st.session_state.selected_file = None
    st.session_state.edit_mode = False

def get_metadata(path):
    """Return formatted metadata string from os.stat() - reads the file's inode."""
    try:
        info = os.stat(path)
        size = f"{info.st_size / 1024:.1f} KB"
        ext = os.path.splitext(path)[1] or "(none)"
        mtime = datetime.datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M")
        return f"Size: {size}  |  Type: {ext}  |  Modified: {mtime}"
    except OSError:
        return "Metadata unavailable"


# -- Sidebar: file & folder operations ------------------------------------

with st.sidebar:
    st.header("File Operations")

    with st.expander("New File"):
        new_fname = st.text_input("File name (e.g. notes.txt)", key="new_file_name")
        if st.button("Create File") and new_fname:
            p = os.path.join(st.session_state.current_path, new_fname)
            if os.path.exists(p):
                st.error("Already exists.")
            else:
                try:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write("")
                    st.success(f"Created {new_fname}")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with st.expander("New Folder"):
        new_dname = st.text_input("Folder name", key="new_dir_name")
        if st.button("Create Folder") and new_dname:
            p = os.path.join(st.session_state.current_path, new_dname)
            try:
                os.makedirs(p, exist_ok=False)
                st.success(f"Created {new_dname}/")
                st.rerun()
            except FileExistsError:
                st.error("Already exists.")
            except Exception as e:
                st.error(str(e))

    with st.expander("Rename"):
        if st.session_state.selected_file:
            old = os.path.basename(st.session_state.selected_file)
            new_name = st.text_input("New name", value=old, key="rename_input")
            if st.button("Rename") and new_name and new_name != old:
                try:
                    os.rename(st.session_state.selected_file,
                              os.path.join(os.path.dirname(st.session_state.selected_file), new_name))
                    st.session_state.selected_file = None
                    st.success(f"Renamed to {new_name}")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.info("Select a file or folder first.")

    with st.expander("Delete"):
        if st.session_state.selected_file:
            name = os.path.basename(st.session_state.selected_file)
            st.warning(f"Delete **{name}**?")
            if st.button("Confirm Delete"):
                try:
                    if os.path.isdir(st.session_state.selected_file):
                        shutil.rmtree(st.session_state.selected_file)
                    else:
                        os.remove(st.session_state.selected_file)
                    st.session_state.selected_file = None
                    st.success("Deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.info("Select a file or folder first.")


# -- Main layout: left browser + right viewer -----------------------------

left_col, right_col = st.columns([1, 2])

with left_col:
    st.markdown(f"**`{st.session_state.current_path}`**")
    nav1, nav2 = st.columns(2)
    nav1.button("Back", on_click=go_back, use_container_width=True)
    nav2.button("Home", on_click=go_home, use_container_width=True)
    search = st.text_input("Search", placeholder="Filter files...", label_visibility="collapsed")
    st.divider()

    entries = load_directory(st.session_state.current_path)
    for name, is_dir in entries:
        if search and search.lower() not in name.lower():
            continue
        full = os.path.join(st.session_state.current_path, name)
        label = f"[DIR]  {name}" if is_dir else f"[FILE] {name}"
        if st.button(label, key=full, use_container_width=True):
            if is_dir:
                st.session_state.current_path = full
                st.session_state.selected_file = None
                st.session_state.edit_mode = False
                st.rerun()
            else:
                st.session_state.selected_file = full
                st.session_state.edit_mode = False
                st.rerun()

with right_col:
    sel = st.session_state.selected_file
    if sel and os.path.isfile(sel):
        st.subheader(os.path.basename(sel))
        st.caption(get_metadata(sel))
        content, err = open_file(sel)
        if err:
            st.warning(err)
        else:
            if st.session_state.edit_mode:
                edited = st.text_area("Editing", value=content, height=400, key="editor")
                c1, c2 = st.columns(2)
                if c1.button("Save", use_container_width=True):
                    try:
                        save_file(sel, edited)
                        st.session_state.edit_mode = False
                        st.success("Saved!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                if c2.button("Cancel", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()
            else:
                st.code(content, line_numbers=True)
                if st.button("Edit this file"):
                    if is_binary(sel):
                        st.warning("Binary file - cannot edit as text.")
                    else:
                        st.session_state.edit_mode = True
                        st.rerun()
    else:
        st.info("Select a file from the left panel to view its contents.")
