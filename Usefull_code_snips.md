# Calls kernel_density: # KM moved here from a separate md file

# create sample data
# für beispieldata vom

---

# create list of repeating values
importindata(data, 45);

x = np.linspace(min(data["Array"]), max(data["Array"]), data["Array"].shape[0])
sample = data["Array"][:, np.newaxis].astype(int)
# plot histogramm

plot_loghist(data, 500)
---

for bandwidth in np.linspace(0.2, 3, 3):
    kde = getKernelDensityEstimation(data, x, bandwidth=bandwidth)
    plt.plot(x, kde, alpha = 0.8, label = f'bandwidth = {round(bandwidth, 2)}')

---

cv_bandwidth = bestBandwidth(data["Array"])

from statsmodels.nonparametric.kernel_density import KDEMultivariate
from statsmodels.nonparametric.kernel_density import EstimatorSettings
settings = EstimatorSettings(efficient=True)
stats_models_cv = KDEMultivariate(data["Array"], 'c', bw = 'cv_ml', defaults = settings).pdf(x)

---

CV_best_plot(data["Array"])

---

 #plot distribution legend with dg:
 #add dg in list of variables in the funktion Dist.plot_singledata

 dg = data["dg"]

 #than replace

 legend_entries.append(input(f"Please enter the legend entry for scan {scan_nrs[ct]}"))

 #by

 user_input = input(f"Please enter the legend entry for scan {scan_nrs[ct]}")
 legend_entries.append(user_input + " (" + str("{:.2f}".format(float(dg[k]))) + " nm)")

---

Change funktion plot cumulative data and make it uniform cf. title and all instances of cummCn/cummC
create different format plot funktion for cumulative data and a combination of both


def two_scales(ax1, X, Cn, Width, normcummCn, c1):
    ax2 = ax1.twinx()

    ax1.bar(X, Cn, Width, edgecolor=c1)
    #ax1.legend("ABCDEFGHIJKLMNOP")

    ax2.plot(X, normcummCn)
    #ax2.legend("ABCDEFGHIJKLMNOP")
    return ax1, ax2

---

def plot_combidata(data, used_device, scan_nrs):
    """plots the given data, specify measurement to use from sel_Cn array"""
    # seems to work, just needs another axis label to indicate it is cummulative :D
    X = data["X"]
    bar_width = data["bar_width"]
    Cn = data["Cn"]
    cummCn = data["cummCn"]
    used_device = data["used_device"]
    calc_conc_n = data["calc_conc_n"]
    normcummCn = np.zeros_like(cummCn)
    for k in range(len(cummCn)):
        if calc_conc_n[k] > 0:
            normcummCn[k] = cummCn[k]/calc_conc_n[k]
        else:
            normcummCn[k] = cummCn[k]
    plot_nrs = Sup.py_logic_converter(scan_nrs)
    fig, ax = plt.subplots() # height with title 12, without 10

    if len(plot_nrs) == 1:
        k = plot_nrs[0]
        ax1, ax2 = two_scales(ax, X[k, :], Cn[k, :], bar_width[k, :], normcummCn[k, :], 'black')
        legend_entries = [input(f"Please enter the legend entry for scan {scan_nrs[0]}")]
        # scan_nrs is used here on purpose
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        ct = 0
        for k in plot_nrs:
            ax1, ax2 = two_scales(ax, X[k, :], Cn[k, :], bar_width[k, :], normcummCn[k, :], 'black')
            legend_entries.append(input(f"Please enter the legend entry for scan {scan_nrs[ct]}"))
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
            ct += 1
    format_combiplot(fig, ax1, ax2, used_device)
    plt.legend(legend_entries, loc="upper left")

    plt.show()
    return ax1, ax2

---

def format_combiplot(fig, ax1, ax2, used_device):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(18.5 * cm, 10 * cm)
    ax1.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax2.xaxis.set_major_formatter(ticker.ScalarFormatter())
    if used_device in [3, 4, 5]:  # for micrometer instruments TSI LAS + APS, PALAS WELAS
        ax1.set(xscale="log", xticks=[0.5, 1, 2, 5, 10], xticklabels=[0.5, 1, 2, 5, 10],
               xlabel='Particle Diameter / $\mu$m', ylabel='Number Concentration / $\mathregular{1/cm^3}$')
        ax2.set(ylabel="Relative Anzahl")
    else:  # for nanometer instruments SMPS
        ax1.set(xscale="log", xticks=[20, 50, 100, 200, 400, 800], xticklabels=[20, 50, 100, 200, 400, 800],
                xlabel='Particle Diameter / nm', ylabel= 'Number Concentration / $\mathregular{1/cm^3}$') # dN/dlogD$_{p}$
        ax2.set(ylabel='Relative Anzahl')
    # yscale='log', xscale='log', xlabel='$\mathregular{dlog D_p}$ / nm', ylabel='dN / $\mathregular{P/cm^3}$'
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return

---
def get_more_data():
    LAS_data = []
    Frage = input("Do you want to import LAS data? Answer Yes")
    while Frage == "Yes":
        data_identifier = [input(f"Please enter the data_identifier")]
        data_identifier = get_data()
        LAS_data.append(data_identifier)
        Frage = input("Do you still want to import more LAS data? Answer Yes")

    return LAS_data

---

def Calc_all_LAS(LASdata):
    LAS_List_identifier = LASdata
    for k in range(len(LAS_List_identifier)):
        Dist.typical_calculations(LAS_List_identifier[k])


Dist.typical_calculations(LAS_List_identifier[]); #funktioniert einzeln

---

if mathregular is not accepted/not running use

$\\mathregular{1/cm^3}$


---
def plot_calc_conc_n(data, scan_nrs):
    scan_numbers = scan_nrs
    from array import array
    plot_nrs = Sup.py_logic_converter(scan_nrs)
    scans = array("i", data["scan_nr"])
    bar_width = [1]
    calc_conc_n = data["calc_conc_n"]
    fig, ax = plt.subplots()
    if len(plot_nrs) == 1:
        k = plot_nrs[0]
        ax.bar(scans[k], calc_conc_n[k], width=bar_width, edgecolor="black")
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        ct = 0
        for k in plot_nrs:
            ax.bar(scans[k], calc_conc_n[k], width=bar_width, edgecolor="black", alpha=0.5)
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
            ct += 1
    format_conc_plot(fig, ax, scan_numbers)
    plt.show()
    return ax

def format_conc_plot(fig, ax, scan_numbers):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(18.5 * cm, 10 * cm)
    xtick_entries = []
    numbers = scan_numbers
    cb = 0
    for k in numbers:
        xtick_entries.append(input(f"Please enter the xtick entries for measurement {scan_numbers[cb]}"))
        cb += 1
    ax.set(xticks =  numbers, xticklabels=xtick_entries,
            ylabel='Number Concentration / $\mathregular{1/cm^3}$')
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return

---
Kevins Version

def plot_calc_conc_n(data, scan_nrs):
    """ function by Nico"""
    plot_nrs = py_logic_converter(scan_nrs)
    x_axis = range(1, len(scan_nrs) + 1)
    calc_conc_n = data["calc_conc_n"]
    fig, ax = plt.subplots()
    if len(plot_nrs) == 1:
        k = plot_nrs[0]
        ax.scatter(x_axis[k], calc_conc_n[k], edgecolor="black")
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        for k in range(len(plot_nrs)):
            ax.scatter(x_axis[k], calc_conc_n[plot_nrs[k]], edgecolor="black")
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    format_conc_plot(fig, ax, scan_nrs)
    plt.show()
    return ax

    def format_conc_plot(fig, ax, scan_nrs):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(18.5 * cm, 10 * cm)
    xtick_entries = []
    for k in scan_nrs:
        xtick_entries.append(input(f"Please enter the xtick entries for measurement {k}"))
    ax.set(xticks=range(1, len(scan_nrs)+1), xticklabels=xtick_entries,
           ylabel='Number Concentration / $\mathregular{1/cm^3}$')
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return

---

create colormap

from random import randint
colors = []

for i in range(10):
    colors.append('#%06X' % randint(0, 0xFFFFFF))

___
Plot funktion with Median

def plot_singledata(data, scan_nrs):
    """plots the given data, specify measurement to use from sel_Cn array"""
    X = data["X"]
    dg = data["dg"]
    bar_width = data["bar_width"]
    Cn = data["Cn"]
    calc_conc_n = data["calc_conc_n"]
    used_device = data["used_device"]
    plot_nrs = Sup.py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    if len(plot_nrs) == 1:
        legend_entries = []
        k = plot_nrs[0]
        ax.bar(X[k, :], Cn[k, :], width=bar_width[k, :], edgecolor='black')
        plt.axvline(dg[k], color=colors[k])
        user_input = input(f"Please enter the legend entry for scan {scan_nrs[0]}")
        legend_entries.append(user_input + " (" + str("{:.2f}".format(float(dg[k]))) + " nm)")
        # scan_nrs is used here on purpose
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        ct = 0
        for k in plot_nrs:
            ax.bar(X[k, :], Cn[k, :], width=bar_width[k, :], edgecolor='black', alpha=0.5)
            plt.axvline(dg[k], color=colors[k])
            user_input = input(f"Please enter the legend entry for scan {scan_nrs[ct]}")
            legend_entries.append(user_input + " (" + str("{:.2f}".format(float(dg[k]))) + " nm)")
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3" )
            ct += 1
    format_plot(fig, ax, used_device)
    #plt.rcParams['figure.dpi'] = 600
    #plt.rcParams['savefig.dpi'] = 600
    plt.legend(legend_entries)  # , loc='upper left')
    # move this into format_plot ?
    fileaddition = input("Please enter a fileaddition")
    #data_identifier = Sup.get_variable_name(data)
    path = data["filename"][:-4] + "_" + fileaddition + ".png"
    # path = data["filename"][:-4] + "_" + data_identifier + "_" + fileaddition + ".png"
    plt.savefig(path, transparent=True)
    plt.show()
    return ax

---

in Particle_analysis.py (einfach ganz unten vor _name_ == _main_:)
def save_session():
    filename = Sup.set_filename()
    path = (f"{filename}" + ".dill")
    dill.dump_session(path)
    return

def load_session():
    path = Sup.get_filename()
    dill.load_session(path)
    return

ganz oben im gleichen Skript:
import dill

unter get_filenames in Sup.py

def set_filename():
    """set filename via UI"""
    popup = Tk()
    popup.attributes('-topmost', 1)
    popup.withdraw()
    filename = asksaveasfilename(filetypes=(("All Files", ""), ("png file", ".png"), ("csv file", ".csv"),
                                            ("dill file", ".dill")))
    print(filename)
    return filename

in Sup einfach die Zeile
from tkinter.filedialog import askopenfilename, askopenfilenames
ersetzen durch:
from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename

---
in order to plot all measurment at once use:

for i in range(1, "number of mesurments" + 1)
    plot singledata(data, [i])


def plot_singledata(data, scan_nrs):
    """plots the given data, specify measurement to use from sel_Cn array"""
    X = data["X"]
    bar_width = data["bar_width"]
    Cn = data["Cn"]
    dg = data["dg"]
    calc_conc_n = data["calc_conc_n"]
    used_device = data["used_device"]
    plot_nrs = Sup.py_logic_converter(scan_nrs)
    fig, ax = plt.subplots()  # height with title 12, without 10
    if len(plot_nrs) == 1:
        legend_entries = []
        k = plot_nrs[0]
        ax.bar(X[k, :], Cn[k, :], width=bar_width[k, :], edgecolor='black')
        user_input = f"{k}" #input(f"Please enter the legend entry for scan {scan_nrs[0]}")
        legend_entries.append(user_input + " (" + str("{:.2f}".format(float(dg[k]))) + " nm)")
        # scan_nrs is used here on purpose
        print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3")
    else:
        legend_entries = []
        ct = 0
        for k in plot_nrs:
            ax.bar(X[k, :], Cn[k, :], width=bar_width[k, :], edgecolor='black', alpha=0.5)
            user_input = f"{k}" #input(f"Please enter the legend entry for scan {scan_nrs[ct]}")
            legend_entries.append(user_input + " (" + str("{:.2f}".format(float(dg[k]))) + " nm)")
            print(f"scan {k} conc. = " + "{:e}".format(float(calc_conc_n[k])) + " P/cm" + u"\u00B3" )
            ct += 1
    format_plot(fig, ax, used_device)
    #plt.rcParams['figure.dpi'] = 600
    #plt.rcParams['savefig.dpi'] = 600
    plt.legend(legend_entries)  # , loc='upper left')
    # move this into format_plot ?
    fileaddition = f"Scan_{scan_nrs[0]}" #input("Please enter a fileaddition")
    #data_identifier = Sup.get_variable_name(data)
    path = data["filename"][:-4] + "_" + fileaddition + ".png"
    # path = data["filename"][:-4] + "_" + data_identifier + "_" + fileaddition + ".png"
    plt.savefig(path, transparent=True)
    plt.show()
    return ax

def format_plot(fig, ax, used_device):
    cm = 1 / 2.54  # inches to cm
    fig.set_size_inches(18.5 * cm, 10 * cm)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    if used_device in [3, 4, 5]:  # for micrometer instruments TSI LAS + APS, PALAS WELAS
        ax.set(xscale='log', xticks=[100, 200, 400, 800, 1600, 3200], xticklabels=[100, 200, 400, 800, 1600, 3200],
               xlabel='Particle Diameter / nm',
               ylabel='Number Concentration / $\mathregular{1/cm^3}$')
    else:  # for nanometer instruments SMPS
        ax.set(xscale='log', xticks=[20, 50, 100, 200, 400, 800], xticklabels=[20, 50, 100, 200, 400, 800],
               xlabel='Particle Diameter / nm',
               ylabel='Number Concentration / $\mathregular{1/cm^3}$') # dN/dlogD$_{p}$
    # yscale='log', xscale='log', xlabel='$\mathregular{dlog D_p}$ / nm', ylabel='dN / $\mathregular{P/cm^3}$'
    # plt.title(input("Please enter the title of the figure"), wrap=True, y=1.08)
    fig.subplots_adjust(top=0.95)  # 0.8 when title is active, when not 0.95 looks good also change figsize!
    return

---

# Kevin Start

#@home
jupyter notebook --notebook-dir=C:/UniStuff/Code/Python/py_particleanalysis 
jupyter notebook --notebook-dir=Z:/Projects/AeroCal/Measurements/

#@FhG
jupyter notebook --notebook-dir=I:/Muenchen/05_Analytics_Bioaerosole/Aerosol/
run C:/Users/kevin.maier/PycharmProjects/py_particleanalysis/particle_analysis.py