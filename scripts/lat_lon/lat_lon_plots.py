from src.common import * 
from src.lat_lon_utils import sims_dict
from src.lat_lon_utils import DY3DIR
import src.plot_utils as p_utils
import iris


p_utils.apply_plot_style()

sims = ll.find_sims([DY3DIR])
names = ll.get_sim_ids(sims_dict)


def load_data_test(): 
    siminfo = sims[names[0]]
    variables = ['stratiform_rainfall_flux', 'stratiform_snowfall_flux']
    vars = [
        iris.Constraint(name=v) for v in variables
    ]

    cube = ll.load_sim_timerange(siminfo, start='2020-06-01', end='2020-06-02', streams=['b'],
                                constraint=vars )

    rain = cube.extract('stratiform_rainfall_flux')[1]


    rain_da = xr.DataArray.from_iris(rain)
    rain_1 = rain_da.isel(time=0)

    # plt.colorbar(im, ax=axs, orientation='vertical')
    da_filtered = rain_1.sel(latitude=slice(0, 40), longitude=slice(50, 100))

    slanted = ll.slanted_mask(da_filtered, start=(65, 15), end=(75, 20), width=2)

    fig, axs = plt.subplots(subplot_kw={'projection':ccrs.PlateCarree(central_longitude=0)})
    
    im = slanted.plot.imshow(ax=axs, transform=ccrs.PlateCarree(), x='longitude', y='latitude', add_colorbar=True)
    axs.coastlines()

    plt.savefig('figs/angled-tsect')
    plt.close()

load_data_test()