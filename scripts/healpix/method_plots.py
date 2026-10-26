from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cartopy.feature as cf
import cartopy.crs as ccrs
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
from pathlib import Path
from scipy.stats import gaussian_kde
import src.healpix.hp_models as models 
import src.plot_utils as p_utils


p_utils.apply_plot_style()

def plot_subregion_map(ax, region_cfg, subregion_dict):
    """Map showing the analysis region and various sub-regions sub-box."""
    # Convert WAM lon to [-180, 180] for the map extent
    main_lon_min = region_cfg['lon_min'] - 360 if region_cfg['lon_min'] > 180 else region_cfg['lon_min']
    main_lon_max = region_cfg['lon_max']
    main_lat_min = region_cfg['lat_min']
    main_lat_max = region_cfg['lat_max']

    buf_lon_min = region_cfg['buf_lon_min']
    buf_lon_max = region_cfg['buf_lon_max']
    buf_lat_min = region_cfg['buf_lat_min']
    buf_lat_max = region_cfg['buf_lat_max']


    proj = ccrs.PlateCarree()

    ax.set_extent([buf_lon_min, buf_lon_max, buf_lat_min, buf_lat_max],
                  crs=proj)
    ax.coastlines(linewidth=0.8)
    ax.add_feature(cf.BORDERS, linewidth=0.5)
    ax.add_feature(cf.LAND, facecolor='lightgrey', alpha=0.4)
    # sahel_land = ax.add_feature(cf.LAND, facecolor='sandybrown', alpha=0.3, zorder=1)

    crs = ccrs.PlateCarree()
    
    # ax.add_patch(mpatches.Rectangle(
    #     (buf_lon_min, buf_lat_min), 
    #     buf_lon_max - buf_lon_min, buf_lat_max - buf_lat_min, 
    #     linewidth=2, edgecolor='black', facecolor='none', transform=proj,
    #       label='', linestyle='--',

    # ))

    
    subregion_names = subregion_dict.keys()
    for sr in subregion_names: 
        sr_cfg = subregion_dict[sr]
        sr_lon_min = sr_cfg['lon_min'] - 360 if sr_cfg['lon_min'] > 180 else sr_cfg['lon_min']
        sr_lon_max = sr_cfg['lon_max']
        sr_lat_min = sr_cfg['lat_min']
        sr_lat_max = sr_cfg['lat_max']

        sr_color   = sr_cfg['color']

        ax.add_patch(mpatches.Rectangle(
                (sr_lon_min, sr_lat_min),
                sr_lon_max - sr_lon_min, sr_lat_max - sr_lat_min,
                linewidth=2, edgecolor=sr_color, facecolor='none',
                alpha=0.8, transform=proj, label=sr,
            ))

        text_coords = (sr_lon_min + 0.2, sr_lat_max - 2)
        ax.text(*text_coords, s=sr, color=sr_color)

    # ax.legend(loc='lower left')
    # ax.set_title(f'Analysis regions')
    ax.set_xticks(np.arange(main_lon_min - 5, main_lon_max + 10, 10), crs=ccrs.PlateCarree())
    ax.set_yticks(np.arange(main_lat_min - 5, main_lat_max + 5, 5), crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter())
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.grid(True, alpha=0.1)
    # plt.savefig('analysis_region.png', bbox_inches='tight')

def plot_map(region_cfg, region_display, subregion_dict):
    fig_map, ax_map = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()}, figsize=(6, 5))
    plot_subregion_map(ax_map, region_cfg, region_display, subregion_dict)
    fig_map.tight_layout()
    p_utils.centre_legend_above(fig_map, ax_map, ncols=5)
    path = f'figs/{region_display}_analysis_region'
    fig_map.savefig(path)
    fig_map.savefig(path + '.png')
    print(f'Saved {path}')
    plt.close(fig_map)


MODEL_NAMES, REGION_CFG, COLORS = p_utils.plot_var_setup(region='india')
region_display = models.REGIONS['india']['display']
subregion_dict  = models.INDIA_REGIONS
plot_map(REGION_CFG, region_display, subregion_dict)