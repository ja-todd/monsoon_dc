import xarray as xr 
import numpy as np 
import matplotlib.pyplot as plt 
import src.hp_models as models 
import src.hp_utils as utils 
import src.plot_utils as p_utils 
import earthkit.plots as ekp
import cartopy.crs as ccrs 
import cartopy.feature as cfeature
import colormaps as cm
import matplotlib.colors as mcolors 
import pandas as pd
import src.general_utils as g_utils 
import matplotlib.tri as mtri


p_utils.apply_plot_style()


MODEL_NAMES, REGION_CFG, COLORS = p_utils.plot_var_setup(region='tropics_wide')

models_dict = models.models_name_dict
mnames = [models.models_name_dict[name]['path_id'].split('/')[1] for name in MODEL_NAMES]

def tropics_wide_winds_rainfall(region_cfg): 
    proj = ccrs.PlateCarree()
    
    pr_cache = {}
    ds3h_cache = {}
    for mname in mnames:
        ds1h = utils.open_region_1h_dataset(mname, region_cfg)
        ds1h_jjas = utils.filter_season(ds1h, season='jjas')
        pr_cache[mname] = (ds1h_jjas.pr.resample(time='1D').mean() * 86400).mean('time').compute()

        ds3h = utils.open_region_dataset(mname, region_cfg)
        ds3h_cache[mname] = utils.filter_season(ds3h, season='jjas')

    p_levels = [925, 850, 600, 500, 200]
    for p_level in p_levels: 
        fig, axs = plt.subplots(2, 2, figsize=(15, 5), subplot_kw={"projection": proj},\
                                 constrained_layout=True)
        ax1, ax2, ax3, ax4 = axs.flatten()
        print("fig set up")
        for print_name, mname, ax in zip(MODEL_NAMES, mnames, axs.flatten()): 
            ds3h_jjas = ds3h_cache[mname]
            pr = pr_cache[mname].values
            u = ds3h_jjas['ua']
            v = ds3h_jjas['va']
            
            u_p = u.sel(pressure=p_level)
            v_p = v.sel(pressure=p_level)
            u_pt   = u.sel(pressure=p_level).mean('time', keep_attrs=True)
            v_pt   = v.sel(pressure=p_level).mean('time', keep_attrs=True)
            wnd_p = np.hypot(u_p, v_p).mean(dim='time', keep_attrs=True)

            print("precip computed")
            # positions, with longitude as -180..180 so -20..100 is continuous
            lon_c = ((u_pt.lon.values + 180) % 360) - 180
            lat_c = u_pt.lat.values
            uu, vv, ww = u_pt.values, v_pt.values, wnd_p.values

            # thin the arrows by averaging onto a coarser HEALPix level (nested ordering)
            dz = 2                                   # zoom 6 -> 4: about 3.7° spacing; use 1 for denser, 3 for sparser
            coarse = u_pt.cell.values >> (2 * dz)
            uniq, inv = np.unique(coarse, return_inverse=True)
            n = np.bincount(inv)
            def cmean(x):
                return np.bincount(inv, weights=x) / n
            la, lo = cmean(lat_c), cmean(lon_c)      # fine here since the region doesn't cross the +-180 seam
            ua, va = cmean(uu), cmean(vv)

            ax.set_extent([-39, 99, 0.1, 40], crs=proj)
            levels = [0, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 20]          # your levels

            cmap = plt.get_cmap("PuBuGn", len(levels))          # one colour per bin, plus one for extend="max"
            norm = mcolors.BoundaryNorm(levels, cmap.N, extend="max")
            cf = ax.tricontourf(lon_c, lat_c, pr, levels = levels,
                                cmap=cmap, norm=norm, extend="max", transform=proj)
            scale=75
            if p_level == 200: 
                scale = 250
            # if p_level in [925, 850, 200]: 
            #     scale = 700
            q = ax.quiver(lo, la, ua, va, transform=proj, color="black",
                        pivot="middle", scale=scale, scale_units='inches', width=0.002)
            

            ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
            ax.add_feature(cfeature.BORDERS, linewidth=0.3)
            ax.set_title(f'{print_name}')
            gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="grey", alpha=0.6)
            gl.top_labels = gl.right_labels = False

        arrow_thresh = 15
        if p_level == 200: 
            arrow_thresh = 30
        ax4.quiverkey(q, -0.1, 1.1, arrow_thresh , f"{arrow_thresh}" + r" m s$^{-1}$", labelpos="E", coordinates="axes")
        
        # plt.subplots_adjust(hspace=-0.1)
        cbar_ax = fig.add_axes([0.9, 0.1, 0.02, 0.8]) 
        cb = fig.colorbar(cf, cax=cbar_ax)
        cb.set_label("Daily mean precip (mm)"); cb.minorticks_off()
        p_utils.match_colorbar_to_axes(fig, cb, axs, width_fraction=1)
        plt.savefig(f'figs/JJAS_pr_{p_level}hPa_wind_TROPICS')
        plt.close()


def get_days_from_date(n_days): 
    """
    get the n_days either side (and including) a date
    """
    date = pd.Timestamp(date).normalize()
    date_range = pd.date_range(date - pd.Timedelta(days=n_days), 
                               date + pd.Timedelta(days=n_days))
    
    return date_range.date




def pseudo_onset_plot(region_cfg, dates_list, p_levels, central_dates, surrounding_days:int): 
    """
    """
    
    proj = ccrs.PlateCarree()
    ds3h_cache = {}

    print("building dataset cache")
    for mname in mnames:

        ds3h = utils.open_region_dataset(mname, region_cfg, zoom=7)
        ds3h_cache[mname] = ds3h


    print("Dataset cache built, looping now")

    for mname, print_name in zip(mnames, MODEL_NAMES): 
        print(f"Plotting for {mname}: ")

        fig, axs = plt.subplots(len(p_levels), len(central_dates), 
                                figsize=(17, 14), subplot_kw={"projection": proj},\
                                        constrained_layout=True)
        fig.get_layout_engine().set(w_pad=0.02, h_pad=-0.1, wspace=0, hspace=-0.1)

        
        ds3h = ds3h_cache[mname].sel(time=dates_list)
        ds3h = ds3h[['ua', 'va', 'hur', 'orog']]
        print("     Looping over pressure levels: p_levels ")
        orography = ds3h.orog
        

        for i, p_level in enumerate(p_levels):
                print(i)
                print(f"         {p_level}hPa selected")
                # axs[i, 0].set_ylabel(f'{p_level}hPa')  
                axs[i, 0].text(-0.08, 0.5, f'{p_level} hPa', transform=axs[i, 0].transAxes, 
                               rotation='vertical', va='center', ha='center')

                for j, date in enumerate(central_dates):
                        print(f"             {date} period")
                        axs[0, j].set_title(f'{date}')
                        ax = axs[i, j]

                        date_range = (g_utils.get_days_from_date(date, surrounding_days))
                        ds3h_date = ds3h.sel(time=date_range)
                    
                    
                        u_p = ds3h_date.ua.sel(pressure=p_level)
                        v_p = ds3h_date.va.sel(pressure=p_level)
                        u_pt = u_p.mean(dim='time').where(orography <= 1000)
                        v_pt = v_p.mean(dim='time').where(orography <= 1000)
                        wnd_pt = np.hypot(u_p, v_p).mean(dim='time')
                        rh = ds3h_date.hur.sel(pressure=p_level).mean(dim='time')

                        wnd_pt = wnd_pt.where(orography <= 1000)
                        rh     = rh.where(orography <= 1000)
                        

                        
                        lon_c = ((u_pt.lon.values + 180) % 360) - 180
                        lat_c = u_pt.lat.values
                        uu, vv, ww = u_pt.values, v_pt.values, wnd_pt.values
                        la, lo, ua, va = utils.coarsen_healpix(\
                                            u_pt.cell.values, 7, 4.0, lat_c, lon_c, uu, vv)
                        
                         #### Plotting
                        ax.set_extent([65, 104, 4, 32], crs=proj)
                        levels = np.arange(0, 105, 5)  
            
                        cmap = plt.get_cmap('RdYlBu', len(levels))     
                        norm = mcolors.BoundaryNorm(levels, cmap.N, extend="max")

                        rh_vals = rh.values
                        bad = ~np.isfinite(rh_vals)
                        tri = mtri.Triangulation(lon_c, lat_c)
                        tri.set_mask(bad[tri.triangles].any(axis=1))

                        cf = ax.tricontourf(tri, np.where(bad, 0, rh_vals), levels = levels,
                                            cmap=cmap, norm=norm, transform=proj)
                        ax.tricontourf(lon_c, lat_c, bad.astype(float), levels=[0.5, 1.5], 
                                       colors='grey', transform=proj, zorder=1.5)
                        scale=40
                        
                        q = ax.quiver(lo, la, ua, va, transform=proj, color="black",
                                    pivot="middle", scale=scale, scale_units='inches',
                                     units='inches', width=0.04)
                        
            
                        ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
                        ax.add_feature(cfeature.BORDERS, linewidth=0.3)
                        
                        gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="grey", alpha=0.6)
                        gl.top_labels = gl.right_labels = gl.bottom_labels = gl.left_labels =  False
                        
                    # arrow_thresh = 15
                    # if p_level == 200: 
                    #     arrow_thresh = 30
                    # ax4.quiverkey(q, -0.1, 1.1, arrow_thresh , f"{arrow_thresh}" + r"m s$^{-1}$", labelpos="E", coordinates="axes")
                
        # plt.subplots_adjust(hspace=0, wspace=0)
        plt.suptitle(f'{print_name}', fontweight='bold', fontsize=20, y=1.02)
        cbar_ax = fig.add_axes([0.9, 0.1, 0.02, 0.8]) 
        cb = fig.colorbar(cf, cax=cbar_ax, drawedges=True)
        cb.set_label("RH (%)"); cb.minorticks_off()
        p_utils.match_colorbar_to_axes(fig, cb, axs, width_fraction=0.7)
        pos = cbar_ax.get_position()
        arrow_thresh = 5
        ax.quiverkey(q, pos.x0 + pos.width / 2, pos.y0 - 0.07,
                    arrow_thresh, f"{arrow_thresh}" + r" m s$^{-1}$",
                    labelpos="S", coordinates="figure")
        plt.savefig(f'figs/IM_pseudo_onset_{mname}_{(surrounding_days*2) + 1}_period')
        plt.close()


def stacked_winds(region_cfg, p_levels): 
    proj = ccrs.PlateCarree()
    ds3h_cache = {}

    print("building dataset cache")
    for mname in mnames:

        ds3h = utils.open_region_dataset(mname, region_cfg, zoom=7)
        ds3h = utils.filter_season(ds3h, season='jjas')
        ds3h_cache[mname] = ds3h


    print("Dataset cache built, looping now")
    fig, axs = plt.subplots(len(p_levels), len(MODEL_NAMES), 
                                    figsize=(17, 14), subplot_kw={"projection": proj},\
                                            constrained_layout=True)
    fig.get_layout_engine().set(w_pad=0.02, h_pad=-0.1, wspace=0, hspace=-0.1)
    ax1, ax5, ax9, ax13 = axs[0, 0], axs[1, 0], axs[2, 0], axs[3, 0]
    label_axes = [ax1, ax5, ax9, ax13]
    for (i, mname), print_name in zip(enumerate(mnames), MODEL_NAMES): 
        print(f"Plotting for {print_name}: ")
        axs[0, i].set_title(print_name)
    
        ds3h = ds3h_cache[mname]

        ds3h = ds3h[['ua', 'va', 'hur', 'orog', 'ta']]
        print("     Looping over pressure levels: p_levels ")
        orography = ds3h.orog
        

        for j, p_level in enumerate(p_levels):
            print(i)
            print(f"         {p_level}hPa selected")
            # axs[i, 0].set_ylabel(f'{p_level}hPa')  
            ax = axs[j, i]
            

            u_p = ds3h.ua.sel(pressure=p_level)
            v_p = ds3h.va.sel(pressure=p_level)
            u_pt = u_p.mean(dim='time').where(orography <= 1000)
            v_pt = v_p.mean(dim='time').where(orography <= 1000)
            wnd_pt = np.hypot(u_p, v_p).mean(dim='time')
            rh = ds3h.hur.sel(pressure=p_level).mean(dim='time')
            temp = ds3h.ta.sel(pressure=p_level)
            Rd, cp = 287.04, 1005
            t_pot = (temp*(1000/p_level)**(Rd/cp)).mean(dim='time')

            wnd_pt = wnd_pt.where(orography <= 1000)
            rh     = rh.where(orography <= 1000)
            t_pot  = t_pot.where(orography <= 1000)
            

            
            lon_c = ((u_pt.lon.values + 180) % 360) - 180
            lat_c = u_pt.lat.values
            uu, vv, ww = u_pt.values, v_pt.values, wnd_pt.values
            la, lo, ua, va = utils.coarsen_healpix(\
                                u_pt.cell.values, 7, 4.0, lat_c, lon_c, uu, vv)
            
                #### Plotting
            ax.set_extent([65, 104, 4, 32], crs=proj)
            # levels = np.arange(0, 105, 5)   ## use if rh
            levels = np.arange(300, 332, 2)


            # 'RdYlBu' # use if RH
            cmap_choice = 'hot_r'
            cmap = plt.get_cmap(cmap_choice, len(levels))     
            norm = mcolors.BoundaryNorm(levels, cmap.N, extend="max")


            
            rh_vals = t_pot.values # change to rh.values if RH

            bad = ~np.isfinite(rh_vals)
            tri = mtri.Triangulation(lon_c, lat_c)
            tri.set_mask(bad[tri.triangles].any(axis=1))

            cf = ax.tricontourf(tri, np.where(bad, 0, rh_vals), levels = levels,
                                cmap=cmap, norm=norm, transform=proj)
            ax.tricontourf(lon_c, lat_c, bad.astype(float), levels=[0.5, 1.5], 
                            colors='grey', transform=proj, zorder=1.5)
            scale=40
            
            q = ax.quiver(lo, la, ua, va, transform=proj, color="black",
                        pivot="middle", scale=scale, scale_units='inches',
                            units='inches', width=0.04)
            

            ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
            ax.add_feature(cfeature.BORDERS, linewidth=0.3)
            
            gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="grey", alpha=0.6)
            gl.top_labels = gl.right_labels = gl.bottom_labels = gl.left_labels =  False


    for _ax, p_level in zip(label_axes, p_levels):       
        _ax.text(-0.08, 0.5, f'{p_level} hPa', transform=_ax.transAxes, 
                                            rotation='vertical', va='center', ha='center')            
        
    cbar_ax = fig.add_axes([0.9, 0.1, 0.02, 0.8]) 
    cb = fig.colorbar(cf, cax=cbar_ax, drawedges=True)
    # cb.set_label("RH (%)"); cb.minorticks_off()
    cb.set_label(r"$\theta$ [K]"); cb.minorticks_off()
    p_utils.match_colorbar_to_axes(fig, cb, axs, width_fraction=0.7)
    pos = cbar_ax.get_position()
    arrow_thresh = 10
    ax.quiverkey(q, pos.x0 + pos.width / 2, pos.y0 - 0.07,
                arrow_thresh, f"{arrow_thresh}" + r" m s$^{-1}$",
                labelpos="S", coordinates="figure")
    plt.savefig(f'figs/IM_JJAS_stacked_winds')
    plt.close()

     
def lat_section(da, lon_min, lon_max, lat_bins):
        """time mean, longitude-sector mean, binned in latitude -> (pressure, lat_bins)"""
        da = da.mean('time').compute()
        lon = da.lon % 360
        da = da.isel(cell=((lon >= lon_min) & (lon <= lon_max)).values)
        return da.groupby_bins('lat', lat_bins).mean()

def to_p(da, p_new):
            return da.sortby('pressure').interp(pressure=p_new).values



def vertical_structure(region_cfg, low_lat, high_lat, lon_bounds:list, lat_spacing=1): 
    """
    Plot the vertical structure of any region 
    """
    lat_bins = np.arange(low_lat, high_lat, lat_spacing)
    lon_min, lon_max = lon_bounds[0], lon_bounds[1]
    ds3h_cache = {}
    
    print("building dataset cache")
    for mname in mnames:

        ds3h = utils.open_region_dataset(mname, region_cfg, zoom=7)
        ds3h = utils.filter_season(ds3h, season='jjas')
        ds3h_cache[mname] = ds3h
    
    
        

    print("Dataset cache built, looping now")
    fig, axs = plt.subplots(2, 2, figsize=(13, 10))
    ax1, ax2, ax3, ax4 = axs.flatten()
    for print_name, mname, ax in zip(MODEL_NAMES, mnames, axs.flatten()): 
        print(f"plotting {print_name} data now")
        ds3h = ds3h_cache[mname]
        lat_section_args = lon_min, lon_max, lat_bins

        v   = lat_section(ds3h['va'], lon_min, lon_max, lat_bins)
        # w   = lat_section(ds3h['wap'])      # omega, Pa/s -- check the variable name
        fld = lat_section(ds3h['ua'], lon_min, lon_max, lat_bins)       # field to contour

        lat_mid = np.array([iv.mid for iv in v.lat_bins.values])
        p_new = np.linspace(float(v.pressure.min()), float(v.pressure.max()), 60)

           # (p, lat)

        Rd, g = 287.04, 9.80665

        w = lat_section(ds3h['wa'], *lat_section_args)      # vertical velocity, m/s (positive up)
        T = lat_section(ds3h['ta'], *lat_section_args)      # temperature, K

        p_hPa = w.pressure                                  # pressure levels in hPa
        omega_hPa_s = -(p_hPa * g * w) / (Rd * T)           # hPa/s, positive = descent

        # then use it in place of w/100 in the earlier code, interpolated as before
        w_i = to_p(omega_hPa_s, p_new)
        w_plot = w_i


        v_i, w_i, f_i = to_p(v, p_new), to_p(w, p_new), to_p(fld, p_new)

        # velocity in plotted units: degrees lat per second, and hPa per second
        v_plot = v_i / 111e3
        # w_plot = w_i / 100.0

        cf = ax.contourf(lat_mid, p_new, f_i, levels=np.arange(-10, 10, 1),
                        cmap='RdBu_r', extend='both')
        ax.streamplot(lat_mid, p_new,
                    np.ma.masked_invalid(v_plot), np.ma.masked_invalid(w_plot),
                    color='k', density=1.5, linewidth=0.8, arrowsize=1)
        ax.invert_yaxis()
        ax.invert_xaxis()
        ax.set_ylim(1000, 0)
        ax.set_title(print_name)

    for _ax in [ax1, ax3]: 
        _ax.set_ylabel('Pressure [hPa]')
    for _ax in [ax3, ax4]: 
        _ax.set_xlabel('Latitude [°N]')
    
    cb = fig.colorbar(cf, ax=axs).set_label('u (m s$^{-1}$)')
    plt.savefig('figs/IM_vertical_structure')


def get_multiple_angled_transects(start_lats: list, longitudes: list, angle: int):
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
     


        
    
    







# tropics_wide_winds_rainfall(REGION_CFG)

IM_region = models.REGIONS['india']
central_dates = ['2020-05-25','2020-06-05', '2020-07-05', '2020-08-05']
n_days = 2
dates_list = g_utils.format_date_list(central_dates, n_days=n_days)
p_levels = [600, 750, 850, 925]
# pseudo_onset_plot(IM_region, dates_list, p_levels, central_dates, surrounding_days=n_days)


# stacked_winds(IM_region, p_levels)
# wam_vertical_structure(REGION_CFG, low_lat=4, high_lat=30, lon_bounds=[-20, 20], lat_spacing=1)
vertical_structure(IM_region, low_lat=-5, high_lat=30, lon_bounds=[60, 105], lat_spacing=1)

