"""
Code example
"""

count = 0
for k in [0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 15, 16, 18, 19, 21, 22, 24, 25, 27, 28, 30, 31, 33, 34]:
    dum_Cn[k] = sel_Cn[count]
    dum_X[k] = sel_X[count]
    dum_bar_width[k] = sel_bar_width[count]
    count += 1
count = 0
for k in [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]:
    dum_Cn[k] = mean_C[count]
    dum_X[k] = mean_X[count]
    dum_bar_width[k] = mean_bar_width[count]
    count += 1