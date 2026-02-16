"""
Conc_Data_csv_convert.py

writing of Concentration data to Excel for student internship

Created and modified 2023-06-04 from Dist_Data_csv_convert
@written by Kevin Maier (kevin.r.maier@tum.de)

"""

import csv
import os

import Particle_analysis

data = Particle_analysis.get_data()

el_time, Cn, add_info, filename = data["el_time"], data["Cn"], data["add_info"], data["filename"]

with open(f'{os.path.splitext(filename)[0]}.csv', 'w', encoding='iso-8859-1', newline="") as f:
    writer = csv.writer(f)

    if ["Comment"] in add_info.columns.values:
        comment = "Comment"
    else:
        comment = "Scan Nr"

    for msmt in range(len(Cn)):
        scan_nr = msmt+1
        el_time_row = ["Scan Nr / Comment", "elapsed time", "s"]
        [el_time_row.append(i) for i in el_time[msmt]]
        writer.writerow(el_time_row)
        Cn_row = [f"{add_info[comment][msmt]}", "Conc.", "/cm\u00B3"]
        [Cn_row.append(i) for i in Cn[msmt]]
        writer.writerow(Cn_row)

