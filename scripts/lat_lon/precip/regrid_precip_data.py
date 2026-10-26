import xesmf as xe 
import xarray as xr 
import numpy as np 
import os, sys
import src.lat_lon.lat_lon_utils as ll
from src.lat_lon.lat_lon_utils import sims_dict



imerg_base = '/gws/ssde/j25a/ncas_climate/vol1/users/jtodd/data/imerg7India_sfc_30m/raw'
model_base = "/gws/ssde/j25a/ncas_climate/vol1/users/jtodd/data/glm"

start_print, end_print = '20200601', '20200930'

imerg_grid_file = f'{imerg_base}/ppt_sfc_20200601.nc'



names = ll.get_sim_ids(sims_dict)
base_dir = model_base
region = "INDIA"
start_print, end_print = "20200601", "20200930"

# any one IMERG daily file; only its grid is used
COARSE_MODEL = "glm.n216_GAL9"          # <- the model name to leave out
models = [n for n in names if n != COARSE_MODEL]


def edges_from_centres(c):
    """Cell edges for a 1D regular coordinate."""
    c = np.asarray(c, dtype="float64")
    d = np.diff(c)
    return np.concatenate([[c[0] - d[0] / 2], (c[:-1] + c[1:]) / 2, [c[-1] + d[-1] / 2]])


def with_bounds(ds):
    """Dataset/DataArray with lat, lon and 1D bounds lat_b, lon_b (needed by xesmf)."""
    ds = ds.rename({"latitude": "lat", "longitude": "lon"})
    return ds, edges_from_centres(ds.lat.values), edges_from_centres(ds.lon.values)


def make_target():
    g = xr.open_dataset(imerg_grid_file)
    g, lat_b, lon_b = with_bounds(g[["latitude", "longitude"]])
    return xr.Dataset(
        coords={"lat": g.lat, "lon": g.lon,
                "lat_b": ("lat_b", lat_b), "lon_b": ("lon_b", lon_b)}
    )


def regrid_model(name, target):
    mname = name.split(".")[1]
    in_dir = f"{base_dir}/{mname}/precip/{region}"
    infile = f"{in_dir}/raw/{start_print}_{end_print}.nc"
    outfile = f"{in_dir}/regridded/{start_print}_{end_print}_0p1deg.nc"
    weights = f"{base_dir}/{mname}/weights_to_imerg.nc"

    os.makedirs(os.path.dirname(outfile), exist_ok=True)

    if os.path.exists(outfile):
        print(f"Skipping {name}, already done", flush=True)
        return

    da = xr.open_dataarray(infile, chunks={'time':240})
    da = da.drop_vars([c for c in da.coords if c not in da.dims], errors="ignore")
    da = da * 3600.0                                  # kg m-2 s-1 -> mm/hr
    da.attrs["units"] = "mm/hr"
    da, lat_b, lon_b = with_bounds(da)


    src_grid = xr.Dataset(coords = {"lat": da.lat, "lon": da.lon, 
                                    "lat_b": ("lat_b", lat_b), 
                                    "lon_b": ("lon_b", lon_b)})

    reuse = os.path.exists(weights)
    rg = xe.Regridder(src_grid, target, method="conservative",
                      filename=weights, reuse_weights=reuse)

    out = rg(da, skipna=True, na_thres=0.5)
    out = out.rename({"lat": "latitude", "lon": "longitude"})
    out.name = "precipitation"
    out.attrs["units"] = "mm hr-1"
    out.attrs["regridding"] = "xesmf conservative onto IMERG 0.1 deg grid"

    out.to_netcdf(outfile + ".tmp")
    os.rename(outfile + ".tmp", outfile)

    # quick conservation check (interior domain mean, before vs after)
    print(f"{name}: mean before {float(da.mean()):.4f}, after {float(out.mean()):.4f} mm/hr",
          flush=True)


def main():
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ["SLURM_ARRAY_TASK_ID"])
    if idx >= len(models):
        print(f"Index {idx} beyond {len(models)} models, nothing to do")
        sys.exit(0)
    print(f"Regridding {models[idx]}", flush=True)
    regrid_model(models[idx], make_target())


if __name__ == "__main__":
    main()

