# -*- coding: utf-8 -*-
"""
PALAS_USMPS_csv_convert.py

writing of SMPS data to Excel for student internship

Created 2022-06-20
@written by Kevin Maier (kevin.r.maier@tum.de)

2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
"""

import csv
import os
import PALAS_USMPS_fileread
from Sup import get_filename


filename = get_filename()


X, dX, dlogX, Cn, Cn_dlogX, add_info = PALAS_USMPS_fileread.import_data(filename)

with open(f'{os.path.splitext(filename)[0]}.csv', 'w', encoding='UTF8', newline="") as f:
    writer = csv.writer(f)

    for msmt in range((len(Cn))):
        scan_nr = msmt+1
        x_row = ["Scan Nr", "X", "nm"]
        [x_row.append(i) for i in X[msmt]]
        writer.writerow(x_row)
        dx_row= [scan_nr, "dX", "nm"]
        [dx_row.append(i) for i in dX[msmt]]
        writer.writerow(dx_row)
        dlogx_row = ["Comment", "dlogX", "nm"]
        [dlogx_row.append(i) for i in dlogX[msmt]]
        writer.writerow(dlogx_row)
        Cn_row = [f"{add_info['Comment'][msmt]}", "Conc.", "1/cm^3"]
        [Cn_row.append(i) for i in Cn[msmt]]
        writer.writerow(Cn_row)

