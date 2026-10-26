from src.common import * 
import os 

data_dir = "/gws/ssde/j25a/ncas_climate/vol1/users/jtodd/data/imerg7India_sfc_30m/raw"

def load_imerg(start, end, data_dir=data_dir, **kwargs): 
    """ Load all daily files between start and end (inclusive) """
    days = pd.date_range(start, end, freq='1D')
    files = [f'{data_dir}/ppt_sfc_{d:%Y%m%d}.nc' for d in days]

    print(f"Attempting to load IMERG for date range: {start} -- {end}")
    print(f"First file is {files[0]}")
    
    missing = [f for f in files if not os.path.exists(f)]
    if missing: 
        print(f"Warning: {len(missing)} missing files, e.g. {missing[0]}")
        files = [f for f in files if not f in set(missing)] 

    return xr.open_mfdataset(files, combine='by_coords', **kwargs)