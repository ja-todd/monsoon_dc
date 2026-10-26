
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

def load_box(ds, region_cfg, data_format='hp'):

    lat_coord = 'lat'
    lon_coord = 'lon'

    if data_format != 'hp': 
        lat_coord = 'latitude'
        lon_coord = 'longitude'
        
    
    """Load zarr store and select cells in the Burkina Faso box."""
    lon_min = region_cfg['lon_min'] - 360 if region_cfg['lon_min'] > 180\
                                             else region_cfg['lon_min']
    lon_max = region_cfg['lon_max']
    lat_min = region_cfg['lat_min']
    lat_max = region_cfg['lat_max']

    lon180 = (ds[lon_coord] + 180) % 360 - 180


    mask   = (
        (ds[lat_coord] > lat_min) & (ds[lat_coord] < lat_max) &
        (lon180 > lon_min) & (lon180 < lon_max)
    )
    mask = mask.compute()
    print(f'Cells in box: {mask.values.sum()}')
    return ds, ds.isel(cell=mask)


def diurnal_cycle(da):
    return da.groupby('time.hour').mean(dim=['time', 'cell']),\
          da.groupby('time.hour').std(dim=['time', 'cell'])




def plot_diurnal_cycle(region_cfg, months:list, variable:str, time_res:str):

    ds_cache = g_utils.build_dataset_cache(mnames, region_cfg, 
                                           months, zoom=7, time_res=time_res)
    region_name = region_cfg['display']
    subregion_dict  = models.INDIA_REGIONS
    subregion_names = subregion_dict.keys()
    units = atm_units[variable] if variable in atm_units else ''
    

    fig, axs = plt.subplots(len(MODEL_NAMES), len(months), figsize=(20, 16), 
                        sharey=True, sharex=True) 
    x_label_axis = axs[-1, :]
    for sr in subregion_names: 
        sr_cfg = subregion_dict[sr]
        color = sr_cfg['color']
        axs[0, 0].plot([], [], color=color, label=sr)
    for print_name, (i, mname) in zip(MODEL_NAMES, enumerate(mnames)): 
        axs[i, 0].text(-0.2, 0.5, print_name, transform=axs[i, 0].transAxes, 
                                       rotation='vertical', va='center', ha='center')
        
        print(f"plotting {print_name} data now")
        
        ds_model = ds_cache[mname]

        if 'pressure' in ds_model.dims: 
            ds_model = ds_model.sel(pressure=850)

        # box_ts = {sr: load_box(ds_model, cfg)[1][variable].}

        for (j, month),  in zip(enumerate(months)): 
            
            month_name = g_utils.monthDict[month]
            ds = utils.filter_season(ds_model, [month])
            axs[0, j].set_title(month_name)
            ax = axs[i, j]
            for sr in subregion_names: 
                sr_cfg = subregion_dict[sr]
                color = sr_cfg['color']
                _, ds_box = load_box(ds, sr_cfg)
                var = ds_box[variable]
                if 'kg m-2 s-1' in var.attrs['units']: 
                    var = var * 3600
                mean, std = diurnal_cycle(var)
                ds_ist = mean.assign_coords(hour=(mean.hour + 5.5) % 24).sortby("hour")
                hour = ds_ist.hour
                ax.plot(hour, mean, color=color)
                if variable != 'pr': 
                    ax.fill_between(hour, mean-std, mean+std, alpha=0.2, color=color)
                
    for _ax in x_label_axis: 
        _ax.set_xlim(0, 23)
        _ax.set_xticks(np.arange(0, 24, 3))


    fig.supylabel(f'{variable} ' +  f'[{units}]')
    fig.supxlabel('Hour [UTC]')
    p_utils.centre_legend_above(fig, axs, ncols=len(subregion_names))
    fig.savefig(f'figs/diurnal_cycle_{variable}_{region_name}')





def harmonic_diurnal_cycle_month_sequence(region_cfg, months:list, time_res:str, zoom=8): 
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
    fig, axs = plt.subplots(len(MODEL_NAMES), len(months), figsize=(20, 16), 
                            sharey=True, sharex=True, subplot_kw={'projection': proj}) 

    for print_name, (i, mname) in zip(MODEL_NAMES, enumerate(mnames)): 
        ds = ds_cache[mname]

        row_axs = axs[i, 0] if len(months) > 1 else axs[i]

        row_axs.text(-0.2, 0.5, print_name, transform=row_axs.transAxes, 
                                            rotation='vertical', va='center', ha='center')
                
        print(f"plotting {print_name} data now")


        for (j, month),  in zip(enumerate(months)): 
                    
            month_name = g_utils.monthDict[month]

            ds_m = utils.filter_season(ds, [month])

            column_axs = axs[0, j] if len(months) > 1 else axs[j]

            column_axs.set_title(month_name)
            ax = axs[i, j] if len(months) > 1 else axs[i]
            
                
            
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
            full[ds['cell'].values] = phase_masked.values 


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

    cbar_ax = fig.add_axes([0.9, 0.1, 0.02, 0.8])  # placeholder, will be resized
    cbar = fig.colorbar(pm, cax=cbar_ax, label='Hour [LST]')
    p_utils.match_colorbar_to_axes(fig, cbar, axs, orientation='vertical', 
                                   width_fraction=0.6)        
    plt.savefig(f'figs/diurnal_cycle/{season_string}_first_harmonic_{region_name}')        



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
# plot_diurnal_cycle(REGION_CFG, months=[6, 7, 8, 9], variable='ua', time_res='3h')
# plot_diurnal_cycle(REGION_CFG, months=[6, 7, 8, 9], variable='va', time_res='3h')
# plot_diurnal_cycle(REGION_CFG, months=[6, 7, 8, 9], variable='pr', time_res='1h')


wam_cfg = models.REGIONS['nAfr']
tropics_cfg = models.REGIONS['tropics_wide']
india_cfg = models.REGIONS['india']
# harmonic_diurnal_cycle_month_sequence(wam_cfg, months=[5], time_res='1h')
# harmonic_diurnal_cycle_month_sequence(wam_cfg, months=[9], time_res='1h')
# harmonic_diurnal_cycle_month_sequence(wam_cfg, months=[6], time_res='1h')
# harmonic_diurnal_cycle_month_sequence(wam_cfg, months=[8], time_res='1h')
# harmonic_diurnal_cycle_month_sequence(wam_cfg, months=[7], time_res='1h')
# harmonic_diurnal_cycle_month_sequence(wam_cfg, months=[8], time_res='1h')
# harmonic_diurnal_cycle_month_sequence(REGION_CFG, months=[7], time_res='1h')
# harmonic_diurnal_cycle_month_sequence(REGION_CFG, months=[8], time_res='1h')

harmonic_diurnal_cycle(wam_cfg, months=[6, 7, 8], time_res='1h')
harmonic_diurnal_cycle(india_cfg, months=[6, 7, 8, 9], time_res='1h')
harmonic_diurnal_cycle(tropics_cfg, months=[6, 7, 8, 9], time_res='1h')
