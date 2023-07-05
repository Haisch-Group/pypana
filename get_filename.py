# -*- coding: utf-8 -*-
"""
Script for fetching a filename using an UI

2023-07-05 moved out from particle_analysis.py
@written by Kevin Maier (kevin.r.maier@tum.de)

"""


from tkinter import Tk
from tkinter.filedialog import askopenfilename, askopenfilenames


def get_filename():
    """get one filename via UI"""
    popup = Tk()
    popup.attributes('-topmost', 1)
    popup.withdraw()
    filename = askopenfilename()
    print(filename)
    return filename


def get_filenames():
    """get multiple filenames via UI"""
    popup = Tk()
    popup.attributes('-topmost', 1)
    popup.withdraw()
    filenames = askopenfilenames()
    print(filenames)
    return filenames


if __name__ == "__main__":

    # filename = get_filename()
    filenames = get_filenames()  # also works with only 1 filename