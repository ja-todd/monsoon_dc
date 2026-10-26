from src.common import * 
import src.lat_lon.lat_lon_utils as ll
from src.lat_lon.lat_lon_utils import DY3DIR, sims_dict
import src.plot_utils as p_utils 
from src.imerg.imerg_loaders import load_imerg
from src.regions import location_dict
import os

p_utils.apply_plot_style()
plt.rcParams.update({'axes.spines.right': True, 
                     'lines.linewidth': 3, 
                     'axes.facecolor':  'white',
                     'grid.color': 'white',
                     'axes.grid': False,})


model_base_dir = "/gws/ssde/j25a/ncas_climate/vol1/users/jtodd/data/glm"




region = "INDIA"
start_print, end_print = "20200601", "20200930"

sims = ll.find_sims([DY3DIR])
model_names = ll.get_sim_ids(sims_dict)[:4]



### plot longitude bounds
lon1, lon2 = 65, 85

user = 'jtjasmin'
cache_dir = f'/home/users/{user}/monsoon_dc/data/cache/'
os.makedirs(cache_dir, exist_ok=True)


def cached_time_mean(da, name, lon1, lon2, factor, start_print, end_print): 
    f = f'{cache_dir}/{name}_{lon1}_{lon2}_{start_print}_{end_print}_tmean.nc'
    if os.path.exists(f): 
        return xr.open_dataarray(f).load()
    m = ll.time_mean(da, lon1, lon2, factor)
    m.to_netcdf(f + '.tmp')
    os.rename(f + '.tmp', f)

    return m



    




def plot_orog_precip(): 
    
    imerg = load_imerg("2020-06-01", "2020-09-30")
    imerg_color = 'limegreen'

    print("filtering IMERG by longitude")
    imerg_map = cached_time_mean(imerg.precipitation, "imerg", lon1, lon2, 24, start_print, 
                                end_print)

    print("setting up model precip cache")
    model_precip_cache = {}
    for mname in model_names: 
        access_name = mname.split('.')[1]
        in_dir = f"{model_base_dir}/{access_name}/precip/{region}"
        precip_file = f"{in_dir}/regridded/{start_print}_{end_print}_0p1deg.nc"
        da = xr.open_dataset(precip_file, chunks={'time': 240}).precipitation
        model_precip_cache[mname] = cached_time_mean(da, access_name, lon1, lon2, 24, start_print, 
                                                     end_print)

    print("model precip cache built")
    
    n2560_orog = ll.get_orography(model_names[0])
    orog = n2560_orog.sel(longitude=slice(lon1, lon2))

    print("got orography, setting up figure")
    fig, axs = plt.subplots(2, 2, figsize=(12, 10), sharex=True, sharey=True)
    ax1, ax2, ax3, ax4 = axs.flatten()
    # axt1, axt2, axt3, axt4 = [_ax.twinx() for _ax in axs.flatten()]

    for lo, ax in zip(list(location_dict.keys()), axs.flatten()): 
        # print(ax)
        print(f"plotting for {lo} latitudes")
        lat1, lat2 = location_dict[lo]['latitudes']
        orog_lat_sl = orog.sel(latitude=slice(lat1, lat2))
        orog_mean       = orog_lat_sl.mean(dim='latitude')  
        orog_lons = orog_mean.longitude
        fill      = ax.fill_between(orog_lons, 0, orog_mean, color='grey')
        ax.set_ylim(0, 2000)
        im_pr = ll.latitude_mean(imerg_map, lat1, lat2)
        ax_twin = ax.twinx()
        ax_twin.plot(im_pr.longitude, im_pr, color='blue', linestyle='--')
        ax_twin.set_ylim(0,  50)
        
        ax.set_xlim(lon1, lon2)
        ax.set_title(lo)
        for mname, sim in zip(model_names, list(sims_dict.keys())[:4]): 
            print(f"plotting {mname} precip")
            ds = model_precip_cache[mname]
            ds_mean = ll.latitude_mean(ds, lat1, lat2)
            color = sims_dict[sim]['color']
            ax_twin.plot(ds_mean.longitude, ds_mean, color=color)

        title_names = list(sims_dict.keys())[:4]
        colors = [sims_dict[sim]['color'] for sim in title_names]

    ## plot model name lines    
    for color, name in zip(colors, title_names): 
        ax1.plot([], [], color=color, label=name)

    ## imerg line for legend
    ax1.plot([], [], color='blue', linestyle='--', label='IMERG')

    for _ax in [ax3, ax4]: 
        _ax.set_xlabel('Longitude [$\\degree$ E]')
        _ax.set_xticks(np.arange(lon1, lon2 + 2.5, 2.5))
    for _ax in [ax1, ax3]: 
        _ax.set_ylabel('Height [m]')
    # for _ax in [axt2, axt4]: 
    #     _ax.set_ylabel('Precipitation [mm day$^{-1}$]')
    
    
    p_utils.label_subplots(axs, y_offset=1.03)
    p_utils.centre_legend_above(fig, axs, ncols=5, y_offset=1.06)
    plt.savefig(f'../figs/vertical_structure/precip_orog_{start_print}_{end_print}_mean')



plot_orog_precip()