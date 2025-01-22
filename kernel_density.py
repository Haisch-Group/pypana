import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from sklearn.neighbors import KernelDensity
from statsmodels.nonparametric.bandwidths import bw_silverman, bw_scott, select_bandwidth
from statsmodels.nonparametric.kernel_density import KDEMultivariate
from tqdm import tqdm
import multiprocessing

from unidip import UniDip
import unidip.dip as dip

plt.ion()
plt.show()

def create_array(data, k):
    list = []
    for i in range(len(data["X"][1])):
        #for k in range(len(data["X"][1])):
        innerlist = [data["X"][k][i]] * int(data["Cn"][k][i])
        list.extend(innerlist)
    my_array = np.array(list)
    return my_array



def importindata(data, k):
    data["Array"] = create_array(data, k)
    return data

def plot_loghist(data, bins):
  hist, bins = np.histogram(data["Array"], bins=bins)
  logbins = np.logspace(np.log10(bins[0]),np.log10(bins[-1]),len(bins))
  plt.hist(data["Array"], bins=logbins, alpha=0.4);
  plt.xscale('log')

#Multiprocessing does not work at the moment
#The overhead may be to big (simple funktion with a lot of data)
#def parrallel_score_samples(model, x, thread_count=int(0.875 * multiprocessing.cpu_count())):
    #with multiprocessing.Pool(thread_count) as p:
        #return np.concatenate(p.map(model.score_samples, np.array_split(x[:,np.newaxis], thread_count)))

def getKernelDensityEstimation(data, x, bandwidth = 0.2, kernel = 'gaussian'):
    model = KernelDensity(kernel = kernel, bandwidth=bandwidth, atol=0.3,rtol=0.2)
    model.fit(data["Array"][:, np.newaxis].astype(int))
    log_density = model.score_samples(x[:,np.newaxis])
    return np.exp(log_density)

# tolerance maybe to low?

def bestBandwidth(data, minBandwidth = 0.1, maxBandwidth = 50, nb_bandwidths = 30, cv = 30):
    from sklearn.model_selection import GridSearchCV
    model = GridSearchCV(KernelDensity(),
                        {'bandwidth': np.linspace(minBandwidth, maxBandwidth, nb_bandwidths)}, cv=cv)
    for i in tqdm(range(len(data["Array"]))):
        model.fit(data["Array"][:, None])
    return model.best_params_['bandwidth']

def CV_best_plot(data):
    plt.figure(figsize=(14, 6))
    kde = getKernelDensityEstimation(data, x, bandwidth=cv_bandwidth)
    plt.plot(x, kde, alpha=0.8, label=f'CV bandwidth')
    plt.legend()
    plt.title('Comparative of various bandwidth estimations for KDE');



