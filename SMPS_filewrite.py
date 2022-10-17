# -*- coding: utf-8 -*-
"""
writing of SMPS data to Excel for student internship

Created 2022-06-20
@written by Kevin Maier (kevin.r.maier@tum.de)

2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
"""

import csv
import newSMPS_fileread
import os

filename = newSMPS_fileread.get_filename()
X, bar_width, Cn, time = newSMPS_fileread.import_data(filename)

with open(f'{os.path.splitext(filename)[0]}.csv', 'w', encoding='UTF8', newline="") as f:
    writer = csv.writer(f)

    writer.writerow(X[0])
    # only writes one line of the particle sizes to the file, so when the measuring range is changed during the
    # measurements, this leads to errors

    for msmt in range(len(Cn)):
        writer.writerow(Cn[msmt])
