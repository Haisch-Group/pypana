"""Window for input selection.

This module provides a tkinter file or directory dialogue to select the desired input,
if none is specified at instance creation.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from pypana.readers.base_reader import InputType


def pick_path(input_type: InputType) -> Path:  # pragma: no cover
    """Pick input file or directory path."""
    root = tk.Tk()
    root.withdraw()

    if input_type == InputType.FILE:
        path = filedialog.askopenfilename()
    elif input_type == InputType.DIRECTORY:
        path = filedialog.askdirectory()
    else:
        result = tk.StringVar()
        win = tk.Toplevel(root)
        win.title("Select")
        win.resizable(False, False)

        def _on_file() -> None:
            result.set(filedialog.askopenfilename())
            win.destroy()

        def _on_dir() -> None:
            result.set(filedialog.askdirectory())
            win.destroy()

        tk.Button(win, text="Select File", width=20, command=_on_file).pack(
            padx=20, pady=(20, 5)
        )
        tk.Button(win, text="Select Directory", width=20, command=_on_dir).pack(
            padx=20, pady=(5, 20)
        )
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        root.wait_window(win)
        path = result.get()

    root.destroy()

    if not path:
        raise FileNotFoundError

    return Path(path).resolve()
