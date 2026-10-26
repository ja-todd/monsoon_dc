import iris 
import pandas as pd 
from collections import defaultdict 
from pathlib import Path
from iris.util import equalise_attributes
import xarray as xr 
import numpy as np 



DY3DIR = Path('/gws/ssde/j25b/kscale/DYAMOND3_reruns') 
sims_dict = {
    'RAL3' : {'sim_name': 'glm.n2560_RAL3p3_tuned', 'color': '#0D0C6E'},
    r'GAL9$_{\mathrm{10km}}$' : {'sim_name': 'glm.n1280_GAL9_v2', 'color':'#B79394'},
    r'CoMA9$_{\mathrm{5km}}$'     : {'sim_name': 'glm.n2560_CoMA9_hier_v2', 'color': '#D17A2F'}, 
    r'CoMA9$_{\mathrm{10km}}$' : {'sim_name': 'glm.n1280_CoMA9_v2', 'color':  '#AC2078'},
    r'GAL9$_{\mathrm{60km}}$': {'sim_name': 'glm.n216_GAL9', 'color':  "#206DAC"}

}

############################
## ACCESSING SIMULATIONS ##
############################


def get_sim_ids(sim_dict): 
    names = [list(sim_dict.values())[a]['sim_name'] for a in range(5)]

    return names


def find_sims(dirs): 
    sims = {}
    for d in dirs: 
        patterns = [('*/*/field.pp/apvera.pp/*.apvera_20200120T0000Z.pp', 3), 
                    ('*/*/apvera/*.apvera_20200120T0000Z.pp', 2)]
        for pattern, n_up in patterns: 
            for first_ppa in sorted(d.glob(pattern)): 
                simkey = '.'.join(first_ppa.name.split('.')[:-2])
                basedir = first_ppa.parents[n_up - 1]
                is_global = 'glm' in simkey
                sims[simkey] = {'basedir': basedir, 'is_global': is_global}
    return sims


def _parse_date_from_pp_path(path):
    datestr = path.stem.split('.')[-1].split('_')[1]
    if datestr[-1] == 'Z':
        return pd.to_datetime(datestr, format="%Y%m%dT%H%MZ")
    else:
        return pd.to_datetime(datestr, format="%Y%m%dT%H")


def find_dyamond3_pp_dates_to_paths(basedir):
    """Search for pp_paths with a specific date (N.B. filename sensitive)."""
    pp_paths = sorted(basedir.glob('field.pp/apve*/**/*.pp'))
    if not pp_paths:
        pp_paths = sorted(basedir.glob('apve*/**/*.pp'))
    pp_paths = [p for p in pp_paths if p.is_file()]
    dates_to_paths = defaultdict(dict)
    for path in pp_paths:
        if 'apvere' in path.stem:
            continue
        stream = path.name.split('.')[-2][5]
        dates_to_paths[_parse_date_from_pp_path(path)][stream] = path
    # Only keep completed downloads.
    dates_to_paths = {k: v for k, v in dates_to_paths.items() if len(v) == 4}
    return dates_to_paths


def select_dates(dates_to_paths, start=None, end=None): 
    """Return sorted dates within [start, end] (inclusive). None means open-ended"""
    start = pd.Timestamp(start) if start is not None else None 
    end = pd.Timestamp(end) if end is not None else None
    return [
        d for d in sorted(dates_to_paths)
        if (start is None or d >= start) and (end is None or d <= end)
    ] 


def load_sim_timerange(siminfo, start=None, end=None, streams=None, 
                       constraint=None, concatenate=True): 
    """Load all available timestamps for a simulation within a time window.
    
    Parameters
    -----------
    sims: dict from find_sims 
    simkey : str, key into sims 
    start, end : anything pd.Timestamp accepts (or None for open-ended)
    streams : iterable of stream letters e.g. ['a'] or ['a', 'b']; None = all 
    constraint : optional iris constraint (e.g. iris.Constraint(name='air_temperature'))
    concatenate : merge cubes along time into a single cube per variable 
    """
    dates_to_paths = find_dyamond3_pp_dates_to_paths(siminfo['basedir'])
    dates = select_dates(dates_to_paths, start, end)
    if not dates: 
        raise ValueError('No complete timesteps in that range')
    paths = []
    for d in dates: 
        for s, p in dates_to_paths[d].items(): 
            if streams is None or s in streams: 
                paths.append(p)

    cubes = iris.load(paths, constraint)
    if concatenate: 
        equalise_attributes(cubes)
        cubes = cubes.concatenate()
    return cubes


##############################
#### ANALYSING SIMULATIONS ###
##############################

def slanted_mask(da, start, end, width, lat='latitude', lon='longitude'): 
    lon0, lat0 = start 
    lon1, lat1 = end 
    dx = ((lon1 - lon0 + 180) % 360) - 180  # lon difference between end points
    dy = lat1 - lat0                        # lat difference between end points
    length = np.hypot(dx, dy)               # straight-line length in deg
    ux, uy = dx / length, dy / length       # unit vector along the path

    ### cuts the rectangle down to rectangle containing the strip of (eventually slanted) \
    ### cells
    half = width / 2 
    pad  = half + 0.5 


    lat_v = da[lat].values 
    lon_v = da[lon].values

    rel_lon = ((lon_v - lon0 + 180) % 360) - 180
    rel_lat = lat_v - lat0


    RL, RT = np.meshgrid(rel_lon, rel_lat)
    
    s = RL * ux + RT * uy 
    t = -RL * uy + RT * ux
    mask = (s >=0) & (s <= length) & (t >= -half) & (t < half)

    coords = {lat: da[lat], lon: da[lon]}
    mask_da = xr.DataArray(mask, dims=(lat, lon), coords=coords)
    s_da = xr.DataArray(s, dims=(lat, lon), coords=coords)
    t_da = xr.DataArray(t, dims=(lat, lon), coords=coords)    

    out = da.where(mask_da)

    return out.assign_coords(along=s_da, across=t_da)




def get_orography(sim_id): 
    """sim_id needs to contain the gaussian grid number of the simulation made in
    order to match the orography to 
    """

    print("getting orography")

    orog_base = "/gws/ssde/j25b/kscale/DYAMOND3_reruns/orography/orography-"
    add_on = 'n1280e.nc' if 'n1280' in sim_id else 'n2560e.nc'

    orog_ds = xr.open_dataset(orog_base + add_on)

    return orog_ds.surface_altitude




def time_mean(da, lon1, lon2, per_step_to_day): 
    return (da.sel(longitude=slice(lon1, lon2)).mean('time') * per_step_to_day).load()

def latitude_mean(m, lat1, lat2): 
    b = m.sel(latitude=slice(lat1, lat2))
    w = np.cos(np.deg2rad(b.latitude))
    return b.weighted(w).mean('latitude')