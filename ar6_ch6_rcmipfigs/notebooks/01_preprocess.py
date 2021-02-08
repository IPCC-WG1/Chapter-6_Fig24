# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.3.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Pre-process data: 
#
# This notebook takes the csv files with ERF data (historical and scenario) and converts them into an xarray. 
#
# Notes:
# - Historical emissions are used up until 2019.
# - After this the SSPs are used which results in a jump in ERF because these are not harmonized for 2019.  
#

# %% [markdown]
# ## UPDATE:
#
# - use historic erf up to 2019. 
# - afterwards use SSP
# - Zeb. 
# - Chris 
# - Colors

# %%
from ar6_ch6_rcmipfigs import constants

# %load_ext autoreload
# %autoreload 2

import matplotlib.pyplot as plt
import pandas as pd

# %% [markdown]
# ### Define output paths

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
from ar6_ch6_rcmipfigs.constants import OUTPUT_DATA_DIR

SAVEPATH_DATASET = OUTPUT_DATA_DIR / 'ERF_data.nc'
# just minorGHGs_data here
SAVEPATH_DATASET_minor = OUTPUT_DATA_DIR / 'ERF_minorGHGs_data.nc'
SAVEPATH_DATASET

# %% [markdown]
# ## Load data:

# %% [markdown]
# Data for ERF historical period:

# %%
path_AR_hist = constants.INPUT_DATA_DIR /'AR6_ERF_1750-2019.csv'
path_AR_hist_minorGHG = constants.INPUT_DATA_DIR /'AR6_ERF_minorGHGs_1750-2019.csv'
# use historical up to 2019:
use_hist_to_year = 2019



df_hist = pd.read_csv(path_AR_hist, index_col=0).copy()
df_hist_minor_GHG = pd.read_csv(path_AR_hist_minorGHG, index_col=0).copy()
df_hist.columns

# %% [markdown]
# Find SSP files:

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
path_ssps = constants.INPUT_DATA_DIR / 'SSPs'
paths = path_ssps.glob('*')  # '^(minor).)*$')
files = [x for x in paths if x.is_file()]
files

# %% [markdown]
# Read all SSP files:

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
ERFs = {}
ERFs_minor = {}
nms = []
for file in files:
    fn = file.name  # filename

    _ls = fn.split('_')  # [1]
    nm = _ls[1]
    print(nm)
    print(file)
    if 'minorGHGs' in fn:
        ERFs_minor[nm] = pd.read_csv(file, index_col=0).copy()
    else:
        ERFs[nm] = pd.read_csv(file, index_col=0).copy()
    nms.append(nm)


# %% [markdown]
# ## Replace years up to 2019 by historical ERF

# %% [markdown]
# #### Controle plot before:
#

# %%
for scn in ERFs.keys():
    ERFs[scn].loc[2010:2025]['total_anthropogenic'].plot(label=scn)
    
plt.ylabel('ERF [W/m2]')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# %%
for scn in ERFs_minor.keys():
    ERFs_minor[scn].loc[2010:2025]['HFC-125'].plot(label=scn)
    
plt.ylabel('ERF [W/m2]')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# %%
cols = ERFs['ssp119'].columns
print(cols)
cols_minorGHG = ERFs_minor['ssp119'].columns
print(cols_minorGHG)


# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
for scn in ERFs.keys():
    ERFs[scn].loc[1750:use_hist_to_year] = df_hist[cols].loc[1750:use_hist_to_year]    
    ERFs_minor[scn].loc[1750:use_hist_to_year] = df_hist_minor_GHG[cols_minorGHG].loc[1750:use_hist_to_year]


# %% [markdown]
# #### Controle plot after:

# %%
for scn in ERFs.keys():
    ERFs[scn].loc[2010:2025]['total_anthropogenic'].plot(label=scn)
    
plt.ylabel('ERF [W/m2]')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# %%
for scn in ERFs_minor.keys():
    ERFs_minor[scn].loc[2010:2025]['HFC-125'].plot(label=scn)
    
plt.ylabel('ERF [W/m2]')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# %% [markdown]
# ## Pre-processing: 

# %% [markdown]
# ### Add together aerosol forcing:

# %%
aero_tot = 'aerosol-total'
aero_cld = 'aerosol-cloud_interactions'
aero_rad = 'aerosol-radiation_interactions'
bc_on_snow = 'bc_on_snow'
aero_tot_wbc = 'aerosol-total-with_bc'
for scn in ERFs.keys():
    # add together:
    ERFs[scn][aero_tot] = ERFs[scn][aero_cld] + ERFs[scn][aero_rad]
    ERFs[scn][aero_tot_wbc] = ERFs[scn][aero_tot]+ ERFs[scn][bc_on_snow] 

# %% [markdown]
# ### Compute sum of HFCs

# %%
HFCs_name = 'HFCs'
# list of variables
ls = list(ERFs_minor['ssp370-lowNTCF-aerchemmip'].columns)
# chocose only those with HFC in them
vars_HFCs = [v for v in ls if 'HFC' in v]

vars_HFCs

# %%
for scn in ERFs_minor.keys():
    # sum over HFC variables
    ERFs_minor[scn][HFCs_name] = ERFs_minor[scn][vars_HFCs].sum(axis=1)
    # add row to ERFs as well
    ERFs[scn][HFCs_name] = ERFs_minor[scn][HFCs_name]
ERFs[scn]

# %% [markdown]
# ## Convert to xarray:

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
import xarray as xr


das = []
# loop over scenarios
for scn in ERFs.keys(): 
    # convert to xarray
    ds = ERFs[scn].to_xarray()  # .squeeze()
    # concatubate variables as new dimension
    da = ds.to_array('variable')
    # give scenario name
    da = da.rename(scn)

    das.append(da)

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
# let the new dimension be called scenario:
da_tot = xr.merge(das).to_array('scenario')
# rename the dataset to ERF
da_tot = da_tot.rename('ERF')
# save
da_tot.to_netcdf(SAVEPATH_DATASET)
da_tot.to_dataset()

# %% [markdown]
# ### Save minor GHGs as well:

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
import xarray as xr

das = []
for nm in nms:
    ds = ERFs_minor[nm].to_xarray()  # .squeeze()
    da = ds.to_array('variable')
    da = da.rename(nm)
    das.append(da)

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
da_tot_minor = xr.merge(das).to_array('scenario')
da_tot_minor = da_tot_minor.rename('ERF')
da_tot_minor.to_netcdf(SAVEPATH_DATASET_minor)
da_tot_minor.to_dataset()

# %% [markdown]
# ## Check:

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
da_check = xr.open_dataset(SAVEPATH_DATASET)
da_check

# %%
import matplotlib.pyplot as plt

# %%
for scn in da_check.scenario:
    da_check.sel(variable='total_anthropogenic')['ERF'].sel(scenario=scn).plot(label=scn.values)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', )

# %%
SAVEPATH_DATASET

# %%
