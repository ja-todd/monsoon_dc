import pandas as pd 
import numpy as np 
import src.healpix.hp_utils as utils
import xarray as xr 

monthDict={1:'Jan',
           2:'Feb',
           3:'Mar',
           4:'Apr',
                  5:'May',
                    6:'Jun',
                      7:'Jul',
                        8:'Aug',
                          9:'Sep',
                            10:'Oct',
                              11:'Nov',
                                12:'Dec'}


def format_plot_names(months): 
    month_names = [monthDict[m] for m in months]
    season_string = month_names[0]
    if len(months) > 1: 
        season_string = ''.join(month_names)[::3]

    return month_names, season_string
###------------------------------------###
###        DATETIME FUNCTIONS          ###
###------------------------------------###

def get_days_from_date(date:str, n_days:int): 
    """
    get the n_days either side (and including) a date
    """
    date = pd.Timestamp(date).normalize()
    
    date_range = pd.date_range(date - pd.Timedelta(days=n_days), 
                               date + pd.Timedelta(days=n_days))
    
    return date_range


def format_date_list(dates:list, n_days:int): 
    """
    generate a set of dates that can be used to filter an 
    xarray dataarray, from an array of dates

    generates an n_days either side (and including) each date 
    in a list of dates

    """
    dates_list = [(get_days_from_date(date, n_days)) for date in dates]
    dates_list_formatted = [i.date for i in dates_list]

    return np.concatenate(dates_list_formatted)



###------------------------------------###
###         idk YET FUNCTIONS          ###
###------------------------------------###

def get_multiple_angled_transects(start_lats: list, longitudes: list, angle: int):

    """
    return a 2D array of longitudes and latitudes for a transect on an angle 
    can theoretically construct transects with no spacing in between to get a lat-lon 
    slice at an angle. 

    start_lats: array of (evenly spaced) latitudes 
    longitudes: array of (evenly spaced) longitudes
    angle: angle of the transect in degrees 
    """

    lon_spacing = np.diff(longitudes)[0]
    angle_rad = np.deg2rad(angle)
    lat_increment = np.tan(angle_rad) * lon_spacing
    
    # Create 2D arrays: shape will be (num_paths, num_longitudes)
    num_paths = len(start_lats)
    num_lons = len(longitudes)
    
    lons_2d = np.tile(longitudes, (num_paths, 1))
    lats_2d = np.zeros((num_paths, num_lons))
    
    for i, start_lat in enumerate(start_lats):
        current_lat = start_lat
        for j in range(num_lons):
            lats_2d[i, j] = current_lat
            current_lat += lat_increment
            
    return lons_2d, lats_2d


def build_dataset_cache(model_names, region_cfg, months:list, zoom:int, time_res='3h'): 

    """
    time_res options are '1h' and '3h' (default 3h)
    """

    print("building dataset cache")
    ds_cache = {}
    open_dataset = utils.open_region_dataset

    if time_res=='1h': 
        open_dataset = utils.open_region_1h_dataset

    for mname in model_names:

        ds = open_dataset(mname, region_cfg, zoom)
        ds = utils.filter_season(ds, months)
        ds_cache[mname] = ds

    return ds_cache


def first_harmonic(da, dim='hour'): 
    N = da.sizes[dim]

    c1 = xr.apply_ufunc(
        lambda x: np.fft.rfft(x, axis=1)[..., 1], 
        da, 
        input_core_dims=[[dim]],
        dask='parallelized', 
        output_dtypes=[complex]
    )
    amp = 2 * np.abs(c1) / N 
    phase = (-np.angle(c1) * 24 / (2 * np.pi)) % 24

    return amp, phase


  
def lat_section(da, lon_min, lon_max, lat_bins):
        """time mean, longitude-sector mean, binned in latitude -> (pressure, lat_bins)"""
        da = da.mean('time').compute() if 'time' in da.dims else da
        lon = da.lon % 360
        da = da.isel(cell=((lon >= lon_min) & (lon <= lon_max)).values)
        return da.groupby_bins('lat', lat_bins).mean()


def lon_section(da, lat_min, lat_max, lon_bins): 
    """time mean, latitude-sector mean, binned in latitude -> (pressure, lon_bins)"""
    da = da.mean('time').compute() if 'time' in da.dims else da
    lat = da.lat
    da = da.isel(cell=((lat >= lat_min) & (lat <= lat_max)).values)
    return da.groupby_bins('lon', lon_bins).mean()



###------------------------------------###
###         XARRAY FUNCTIONS           ###
###------------------------------------###


def filter_xarray_percentiles(input_data, lower_percentile, upper_percentile):
    l_quantile = lower_percentile / 100
    u_quantile = upper_percentile / 100 

    data_l_qtile = input_data.quantile(l_quantile, skipna=True)
    data_u_qtile = input_data.quantile(u_quantile, skipna=True)
    filtered = input_data.where((input_data >= data_l_qtile) & (input_data <= data_u_qtile))

    return filtered



###------------------------------------###
###         STATS FUNCTIONS            ###
###------------------------------------###




def binned_stats(x_axis, y_axis, vals, nx=20, statistic='mean', clip=False,
                 x_edges=None, y_edges=None):
    from scipy.stats import binned_statistic_2d
    ny = nx

    if x_edges is not None and y_edges is not None:
        xedges = x_edges
        yedges = y_edges
    elif clip:
        xedges = np.linspace(np.percentile(x_axis, 5), np.percentile(x_axis, 95), nx + 1)
        yedges = np.linspace(np.percentile(y_axis, 5), np.percentile(y_axis, 95), ny + 1)
    else:
        xedges = np.linspace(x_axis.min(), x_axis.max(), nx + 1)
        yedges = np.linspace(y_axis.min(), y_axis.max(), ny + 1)

    stat, _, _, _ = binned_statistic_2d(
        x_axis, y_axis, vals,
        statistic=statistic,
        bins=[xedges, yedges]
    )

    return xedges, yedges, stat

###------------------------------------###
###          MISC FUNCTIONS            ###
###------------------------------------###



def return_kde_plot_inputs(data, kde_type='standard'): 
    from scipy.stats import gaussian_kde
    if kde_type == 'standard': 
        kde  = gaussian_kde(data)
        x    = np.linspace(np.percentile(data, 1), np.percentile(data, 99), 200)

        return x, kde(x)
    
    if kde_type == 'log': 
        """
        return 10**x_log, kde(x_log)
        """
        log_data = np.log10(data[data > 0])
        kde = gaussian_kde(log_data)
        x_log = np.linspace(log_data.min(), log_data.max(), 200)
        
        return 10**x_log, kde(x_log)
    
    if kde_type == 'circular': 
        """ 
        return x_deg, kde(x_deg) * 3
        
        """
        data_rad = np.deg2rad(data)
                        
        # wrap data by concatenating shifted copies to handle circularity
        data_wrapped = np.concatenate([data_rad - 2*np.pi, data_rad, data_rad + 2*np.pi])
        
        kde = gaussian_kde(data_wrapped)
        x_rad = np.linspace(0, 2*np.pi, 200)
    
        return np.rad2deg(x_rad), kde(x_rad)*3
    
    if kde_type == 'reflected': 
        """
        return kde for distribution that is heavily right-skewed
        """
        reflected = np.concatenate([data, -data])
        
        kde = gaussian_kde(reflected)
        x = np.linspace(0, np.percentile(data, 99), 200)
    
        return x, kde(x) * 2