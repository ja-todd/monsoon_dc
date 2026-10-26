import xarray as xr
import src.healpix.hp_utils as utils 
import matplotlib.pyplot as plt 
import src.healpix.hp_models as models
import src.general_utils as g_utils
import src.plot_utils as p_utils 
from src.atmosphere import UNITS as atm_units
import numpy as np
import pandas as pd
import healpy as hp 
import cartopy.crs as ccrs

MODEL_NAMES, REGION_CFG, COLORS = p_utils.plot_var_setup(region='india')
mnames = models.get_model_names()
p_utils.apply_plot_style()



def harmonic_diurnal_cycle(region_cfg, months:list, time_res:str, zoom=8): 
    month_names = [g_utils.monthDict[m] for m in months]
    season_string = month_names[0]
    if len(months) > 1: 
        season_string = ''.join(month_names)[::3]
    region_name = region_cfg['display']
    lon_min, lon_max, lat_min, lat_max = \
            (region_cfg[k] for k in ('lon_min', 'lon_max', 'lat_min', 'lat_max'))
                
    lon_min = lon_min - 360 if lon_min > lon_max else lon_min
    ds_cache = g_utils.build_dataset_cache(mnames, region_cfg, 
                                        months, zoom=zoom, time_res=time_res)
    ds_global = utils.open_1h_dataset(mnames[0], zoom=zoom)
    nside = hp.npix2nside(ds_global.sizes['cell'])
    
    proj = ccrs.PlateCarree()
    fig, axs = plt.subplots(1, len(MODEL_NAMES), figsize=(20, 16), 
                            sharey=True, sharex=True, subplot_kw={'projection': proj}, 
                            tight_layout=True) 

    for print_name, (i, mname), ax in zip(MODEL_NAMES, enumerate(mnames), axs.flatten()): 
        ds_m = ds_cache[mname]

        

        ax.set_title(print_name)
                
        print(f"plotting {print_name} data now")

    
        ax.set_extent([lon_min + 1, lon_max - 1, lat_min + 0.1, lat_max - 0.1], crs=proj)

        print("grouping by precip")
        pr = ds_m['pr'] * 86400
        P  = pr.groupby('time.hour').mean('time') 
        P = P.chunk({'hour': -1})
        amp, phase_utc = g_utils.first_harmonic(P, dim='hour')

        rel_amp = amp / P.mean("hour")
        var_explained = (amp**2 / 2) / P.var("hour")
        mask = (rel_amp > 0.1) & (P.mean("hour") > 0.1)
        
        
        # nside = ds["cell"].attrs["nside"]
        npix  = hp.nside2npix(nside)
        lon, lat = hp.pix2ang(nside, ds_m['cell'].values, nest=True, lonlat=True)

        phase_lst = (phase_utc + xr.DataArray(lon, dims='cell')/15) % 24
        phase_masked = phase_lst.where(mask)

        print("masked phase done")

        full = np.full(npix, np.nan)
        full[ds_m['cell'].values] = phase_masked.values 


        print("full ds done")

        res = hp.nside2resol(nside, arcmin=True) / 60 
        lons = np.arange(lon_min, lon_max, res)
        lats = np.arange(lat_min, lat_max+res, res)
        LON, LAT = np.meshgrid(lons, lats)

        print("LON, LAT meshgrid built")

        idx = hp.ang2pix(nside, LON, LAT, nest=True, lonlat=True)
        img = full[idx]

        cmap, norm = p_utils.diurnal_cycle_cmap()

        print("plotting")
        pm = ax.pcolormesh(LON, LAT, img, cmap=cmap, norm=norm, shading='nearest', transform=proj)

        p_utils.add_map_features(ax)

    plt.suptitle(season_string)
    cbar_ax = fig.add_axes([0.9, 0.1, 0.02, 0.8])  # placeholder, will be resized
    cbar = fig.colorbar(pm, cax=cbar_ax, label='Hour [LST]')
    p_utils.match_colorbar_to_axes(fig, cbar, axs, orientation='vertical', 
                                   width_fraction=0.6)        
    plt.savefig(f'figs/diurnal_cycle/{season_string}_mean_first_harmonic_{region_name}') 