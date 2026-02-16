"""
Dist_Data_csv_convert.py

writing of SMPS data to Excel for student internship

Created 2022-06-20 as PALAS_SMPS2100_csv_convert.py
@written by Kevin Maier (kevin.r.maier@tum.de)

2022-10-17: transferred to gitlab, old versioning was removed, so all referenced files ..._vX were renamed without
    version number
2024-09-02: Changed name to Dist_Data_csv_convert and changed how it works to use the full capability of
    Particle_analysis and enable the conversion of all implemented Distribution Data
"""

import csv
import os

import Particle_analysis
import Sup

data = Particle_analysis.get_data()

X, dX, dlogX, Cn, add_info, filename, used_device = (
    data["X"],
    data["dX"],
    data["dlogX"],
    data["Cn"],
    data["add_info"],
    data["filename"],
    data["used_device"],
)

size_unit = Sup.decide_size_unit(used_device)

with open(
    f"{os.path.splitext(filename)[0]}.csv", "w", encoding="iso-8859-1", newline=""
) as f:
    writer = csv.writer(f)

    if ["Comment"] in add_info.columns.values:
        comment = "Comment"
    else:
        comment = "Scan Nr"

    for msmt in range(len(Cn)):
        scan_nr = msmt + 1
        x_row = ["Scan Nr", "X", size_unit]
        [x_row.append(i) for i in X[msmt]]
        writer.writerow(x_row)
        dx_row = [scan_nr, "dX", size_unit]
        [dx_row.append(i) for i in dX[msmt]]
        writer.writerow(dx_row)
        dlogx_row = [comment, "dlogX", size_unit]
        [dlogx_row.append(i) for i in dlogX[msmt]]
        writer.writerow(dlogx_row)
        Cn_row = [f"{add_info[comment][msmt]}", "Conc.", "1" + "/cm\u00b3"]
        [Cn_row.append(i) for i in Cn[msmt]]
        writer.writerow(Cn_row)
