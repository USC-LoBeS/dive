import matplotlib
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import collections
import numpy as np
import pandas as pd
from math import isnan
import os


## Read this reference to update normalization ...
## https://matplotlib.org/stable/api/colors_api.html

class Colors_csv():
    def __init__(self,stats_csv=None):
        self.csv_flag = None
        self.colors_from_csv = []
        self.stats_csv = stats_csv
        self.map = None

    def intialize(self,log_p_value=False):
        self.df = pd.read_csv(self.stats_csv)
        # if self.df.shape[-1] == 2:
        #     self.col_name = 'P_value'

        if log_p_value:
            self.df['P_value'] = -np.log10(self.df['P_value'])
            self.col_name = 'P_value'
        else:
            self.col_name = 'Value'
            
        self.min_value = self.df[self.col_name].min()       
        self.max_value = self.df[self.col_name].max()  

        
    def assign_colors(self,map,range_value=[],log_p_value=False,threshold=None,output=None,filename='_color_bar.pdf'):
        self.map = map
        self.intialize(log_p_value)
        cmap = matplotlib.cm.get_cmap(map)
        di = {}
        if range_value and len(range_value)>0:
            self.min_value = range_value[0]
            self.max_value = range_value[1]
            self.csv_flag = True
            self.df.sort_values(by=['Labels'],inplace=True)

        norm = mcolors.Normalize(vmin=self.min_value, vmax=self.max_value)
        self.df['Value_n'] = norm(self.df[self.col_name])

        for i,k,j in zip(self.df['Value_n'],self.df['P_value'],self.df['Labels']):
            if self.csv_flag == True:
                if k>threshold:
                    r=g=b=0.5
                else:
                    if i!= None and self.min_value<=i<=self.max_value:  
                        r,g,b,a = cmap(i)
                    if i>self.max_value:
                        r,g,b,a = cmap(self.max_value)
                    if i<self.min_value:
                        r,g,b,a = cmap(self.min_value)
            else:
                r,g,b,a = cmap(i)
            di[j] = [r,g,b]
        clean_dict = {k: di[k] for k in di if not isnan(k)}
        clean_dict = collections.OrderedDict(sorted(clean_dict.items()))
        for k, v in clean_dict.items():
            self.colors_from_csv.append(v)
        self.colors_from_csv = np.asarray(self.colors_from_csv)

        ## Save the color bar images
        
        fig, ax = plt.subplots(figsize=(6, 1))

        print(self.df[self.col_name])
        if output!=None:
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cb = fig.colorbar(sm, cax=ax,orientation='horizontal') # 
            # cb.ax.tick_params(labelsize=10) 
            plt.savefig((output + filename) , bbox_inches='tight', dpi=300)

        return self.colors_from_csv
    