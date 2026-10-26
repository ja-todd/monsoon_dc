import sys, os, datetime 
import pandas as pd 
from src.imerg.process_imerg import read_mfimerg_v7

out_dir = "/gws/ssde/j25a/ncas_climate/vol1/users/jtodd/data/imerg7India_sfc_30m/raw"
os.makedirs(out_dir, exist_ok=True)

dates = pd.date_range(datetime.datetime(2020, 6, 1), datetime.datetime(2020, 9, 30))
lon1, lon2 = 54, 101 
lat1, lat2 = -1, 41

chunk = 10
start = int(sys.argv[1]) * chunk
if start >= len(dates): 
    print(f"Index {start} beyond date range, nothing to do")
    sys.exit(0)

first_time = dates[start]
for first_time in dates[start:start + chunk]: 
    outfile = f'{out_dir}/ppt_sfc_{first_time.strftime('%Y%m%d')}.nc'
    if os.path.exists(outfile): 
        print(f"Skipping {first_time}, already done")
        continue

    print(first_time, flush=True)

    last_time = first_time + datetime.timedelta(hours=23, minutes=59, seconds=59)

    data = read_mfimerg_v7(first_time, last_time, time_method=None, lon_range=(lon1, lon2), 
                        lat_range=(lat1, lat2))
    data.to_netcdf(outfile + ".tmp")
    os.rename(outfile + ".tmp", outfile)
    data.close()