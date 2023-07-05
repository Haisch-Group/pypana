# -*- coding: utf-8 -*-
"""
Script for fetching a filename using an UI

2023-07-05 moved out from particle_analysis.py
@written by Kevin Maier (kevin.r.maier@tum.de)

"""


from tkinter import Tk
from tkinter.filedialog import askopenfilename


def get_filename():
    """get the filename via UI"""
    popup = Tk()
    popup.attributes('-topmost', 1)
    popup.withdraw()
    filename = askopenfilename()
    print(filename)
    return filename


if __name__ == "__main__":

    filename = get_filename()