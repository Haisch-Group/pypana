# -*- coding: utf-8 -*-
"""
writing of SMPS data to Excel for student internship

Created 2022-06-20
@written by Kevin Maier (kevin.r.maier@tum.de)

2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
"""

import csv
import os
import PALAS_SMPS2100_fileread
from tkinter import Tk
from tkinter.filedialog import askopenfilename


def get_filename():
    """get the filename via UI"""
    Tk().withdraw()
    filename = askopenfilename()
    return filename


filename = get_filename()


X, bar_width, Cn, time, comments = PALAS_SMPS2100_fileread.import_data_and_comments(filename)

with open(f'{os.path.splitext(filename)[0]}.csv', 'w', encoding='UTF8', newline="") as f:
    writer = csv.writer(f)

    x_row = ["X", "nm"]
    [x_row.append(i) for i in X[0]]
    writer.writerow(x_row)
    # only writes one line of the particle sizes to the file, so when the measuring range is changed during the
    # measurements, this leads to errors

    for msmt in range((len(Cn))):
        Cn_row = [f"{comments[msmt]}", "1/cm^3"]
        [Cn_row.append(i) for i in Cn[msmt]]
        writer.writerow(Cn_row)

