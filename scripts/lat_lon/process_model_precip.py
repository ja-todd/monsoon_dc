from src.common import *
import iris
import src.lat_lon.lat_lon_utils as ll
from src.lat_lon.lat_lon_utils import DY3DIR, sims_dict

import os, sys, argparse

base_dir = "/gws/ssde/j25a/ncas_climate/vol1/users/jtodd/data/glm"
sims = ll.find_sims([DY3DIR])
names = ll.get_sim_ids(sims_dict)

variables = ['stratiform_rainfall_flux', 'stratiform_snowfall_flux']
vars = [iris.Constraint(name=v) for v in variables]

lon1, lon2 = 54, 101 
lat1, lat2 = -1, 41

start = '2020-06-01'
end   = '2020-09-30'

def make_precip_nc(name, start, end, region:str): 

    t_start = pd.Timestamp(start)
    t_end   = pd.Timestamp(end) + pd.Timedelta(hours=23, minutes=59, seconds=59)

    load_start = t_start - pd.Timedelta(hours=12)
    load_end = pd.Timestamp(end) + pd.Timedelta(hours=12)

    start_print = start.replace('-', '')
    end_print = end.replace('-', '')
    mname = name.split('.')[1] ### needed for the folder

    out_dir = f'{base_dir}/{mname}/precip/{region}'
    os.makedirs(out_dir, exist_ok=True)

    outfile = f'{out_dir}/{start_print}_{end_print}.nc'
    if os.path.exists(outfile): 
        print(f"Skipping {name}, already done")
        return

    siminfo = sims[name]

    cube = ll.load_sim_timerange(siminfo, start=load_start, end=load_end, streams=['b'],
                                constraint=vars )
    srf = cube.extract(variables[0])[1]
    ssf = cube.extract(variables[1])[1]

    rain = srf + ssf
    da = xr.DataArray.from_iris(rain)
    da = da.sel(time=slice(t_start, t_end))
    da = da.sel(longitude=slice(lon1, lon2), latitude=slice(lat1, lat2))
    da.name = "precipitation"
    

    da.to_netcdf(outfile + '.tmp')
    os.rename(outfile + '.tmp', outfile)
        

def main(): 
    parser = argparse.ArgumentParser() 
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--index", type=int, default=None, 
                        help="model index; defaults to $SLURM_ARRAY_TASK_ID")
    args = parser.parse_args() 

    idx = args.index
    if idx is None: 
        idx = int(os.environ["SLURM_ARRAY_TASK_ID"])

    if idx >= len(names): 
        print(f"Index {idx} beyond {len(names)} models, nothing to do")
        sys.exit(0)

    print(f'Running {names[idx]}', flush=True)
    make_precip_nc(names[idx], args.start, args.end, args.region)


if __name__ == "__main__": 
    main()