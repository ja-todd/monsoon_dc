import matplotlib.pyplot as plt 
import src.hp_models as models
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm
from scipy.stats import binned_statistic 
import cartopy.feature as cfeature

def apply_plot_style(): 
    """
    Consistently format plots using rcparams
    """


    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial'],
        'font.size': 15,
        'axes.labelsize': 16,
        'xtick.labelsize': 15,
        'ytick.labelsize': 15,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'xtick.major.size': 6,
        'ytick.major.size': 6,
        'xtick.minor.size': 3,
        'ytick.minor.size': 3,
        'xtick.minor.visible': True,
        'ytick.minor.visible': True,
        'xtick.top': False,       # no top ticks (tmXTOn = False)
        'ytick.right': False,
        'ytick.left': True,     # no right ticks (tmYROn = False)
        'axes.linewidth': 1.5,
        'lines.linewidth': 2,
        'axes.spines.top': False, 
        'axes.spines.right': False,
        'axes.facecolor':  "#EAEAF2E6",
        
        
        'axes.grid': True, 
        'grid.color': '#DEDFE4',
        'grid.alpha': 0.5,
        'figure.labelsize': '15', 
        'font.weight': 'normal', 
        'legend.handlelength': 2, 
        'legend.handletextpad': 0.5, 
        'legend.frameon': False,
        'savefig.format': 'pdf', 
        'savefig.dpi': 300, 
        'savefig.bbox': 'tight'
    })

def match_colorbar_to_axes(fig, cbar, axs, orientation='vertical',
                           width_fraction=0.5, height=0.02, offset=0.02,
                           subfigures=False):
    fig.canvas.draw()
    
    all_axes = np.asarray(axs).flatten()
    
    if subfigures:
        # transform subfigure coordinates to figure coordinates
        boxes = []
        for ax in all_axes:
            bbox = ax.get_window_extent(fig.canvas.get_renderer())
            bbox_fig = bbox.transformed(fig.transFigure.inverted())
            boxes.append(bbox_fig)
    else:
        boxes = [ax.get_position() for ax in all_axes]

    x_min = min(box.x0 for box in boxes)
    x_max = max(box.x1 for box in boxes)
    y_min = min(box.y0 for box in boxes)
    y_max = max(box.y1 for box in boxes)

    cbar.ax.set_in_layout(False)

    if orientation == 'horizontal':
        total_width = x_max - x_min
        cbar_width  = total_width * width_fraction
        cbar_x      = x_min + (total_width - cbar_width) / 2
        cbar_y      = y_min - offset - height
        cbar.ax.set_position([cbar_x, cbar_y, cbar_width, height])

    elif orientation == 'vertical':
        total_height = y_max - y_min
        cbar_height  = total_height * width_fraction
        cbar_x       = x_max + offset
        cbar_y       = y_min + (total_height - cbar_height) / 2
        cbar.ax.set_position([cbar_x, cbar_y, height, cbar_height]) 

def plot_var_setup(region='wam'): 
    """
    Wrapper to make code to set variables for plotting
    at the start of files shorter 

    OUTPUT: 
    model_names, region_cfg, colors

    """
    models_dict = models.models_name_dict
    model_names = list(models_dict.keys())
    region_cfg = models.REGIONS[f'{region}']
    colors = [models.models_name_dict[mname]['color'] for mname in model_names]

    return model_names, region_cfg, colors

def label_subplots(axs, x_offset=-0.1, y_offset=1.02):
    """
    Labels subplots with a), b), c) etc. positioned outside the top left of each axis.
    
    axs: 2D or 1D array of axes (e.g. from plt.subplots)
    x_offset: horizontal position relative to axes (negative = to the left)
    y_offset: vertical position relative to axes (>1 = above)
    """
    axs_flat = np.array(axs).flatten()
    fontsize = plt.rcParams['axes.titlesize']
    
    for i, ax in enumerate(axs_flat):
        label = f'{chr(97 + i)})'  # a), b), c) ...
        ax.text(x_offset, y_offset, label,
                transform=ax.transAxes,
                fontweight='bold',
                fontsize=fontsize,
                ha='left',
                va='bottom')

def centre_legend_above(fig, axs, ncols=4, y_offset=1.02, **legend_kwargs):
    """
    Places a figure legend centred above all subplots.
    
    fig: matplotlib figure
    axs: array of axes
    ncols: number of legend columns
    y_offset: vertical position in figure coordinates (>1 = above axes)
    **legend_kwargs: passed to fig.legend
    """
    fig.canvas.draw()
    
    axs_flat = np.array(axs).flatten()
    
    x_left   = min(ax.get_position().x0 for ax in axs_flat)
    x_right  = max(ax.get_position().x1 for ax in axs_flat)
    y_top    = max(ax.get_position().y1 for ax in axs_flat)
    x_centre = (x_left + x_right) / 2
    
    legend = fig.legend(
        loc='lower center',
        bbox_to_anchor=(x_centre, y_top + (y_offset - 1)),
        ncols=ncols,
        frameon=False,
        **legend_kwargs
    )
    
    return legend

def centre_legend_right(fig, axs, nrows=1, x_offset=1.02, **legend_kwargs):
    """
    Places a figure legend centred vertically to the right of all subplots.

    fig: matplotlib figure
    axs: array of axes
    nrows: number of legend rows (default: 1, i.e. one column)
    x_offset: horizontal position in figure coordinates (>1 = right of axes)
    **legend_kwargs: passed to fig.legend
    """
    fig.canvas.draw()

    axs_flat = np.array(axs).flatten()

    x_left  = min(ax.get_position().x0 for ax in axs_flat)
    x_right = max(ax.get_position().x1 for ax in axs_flat)
    y_bottom = min(ax.get_position().y0 for ax in axs_flat)
    y_top    = max(ax.get_position().y1 for ax in axs_flat)

    y_centre = (y_bottom + y_top) / 2

    legend = fig.legend(
        loc='center left',
        bbox_to_anchor=(x_right + (x_offset - 1), y_centre),
        ncols=1,
        frameon=False,
        **legend_kwargs
    )

    return legend

def setup_regular_plot(rows=1, cols=3): 
    """
    standard plot used in mcs_statistics.py (1 row x 3 columns, to ensure regular size)
    """

    if rows == 1: 
        figsize = (15, 4)
    elif rows == 2: 
        figsize = (15, 9)

    fig, axs = plt.subplots(rows, cols, figsize=figsize)
    label_subplots(axs)

    return fig, axs

def format_jointdist_axis_labelling(subfigs):
    joint_axes_list = [subfig.get_axes()[0] for subfig in subfigs.flatten()]
    marg_x_axes_list = [subfig.get_axes()[1] for subfig in subfigs.flatten()]
    marg_y_axes_list = [subfig.get_axes()[2] for subfig in subfigs.flatten()]

    # Top row: show x tick numbers, but no x-axis label
    for ax in [joint_axes_list[0], joint_axes_list[1]]:
        ax.xaxis.label.set_visible(False)
        # ax.yaxis.label.set_visible(False)

    for ax in [joint_axes_list[1], joint_axes_list[3]]:
        ax.yaxis.label.set_visible(False)
        # ax.xaxis.label.set_visible(False)

    for ax in [marg_x_axes_list[0], marg_x_axes_list[1]]:
        ax.xaxis.label.set_visible(False)
        # ax.yaxis.label.set_visible(False)
    
    
    for ax in [marg_x_axes_list[1], marg_x_axes_list[3]]:
        ax.yaxis.label.set_visible(False)
        ax.xaxis.label.set_visible(False)

    for ax in [marg_y_axes_list[0], marg_y_axes_list[1]]:
        ax.xaxis.label.set_visible(False)

    return joint_axes_list, marg_x_axes_list, marg_y_axes_list

def invert_axes(axs): 
    axs.invert_xaxis()
    axs.invert_yaxis()

    return None 

def build_jointgrid_axes(subfig, ratio=5, space=0.15,
                          density_labels=False, cbar=False, **kwargs):
    gs = subfig.add_gridspec(
        2, 2,
        width_ratios=[ratio, 1], height_ratios=[1, ratio],
        wspace=space, hspace=space
    )
    
    ax_joint = subfig.add_subplot(gs[1, 0])

    ax_marg_x = subfig.add_subplot(
        gs[0, 0],
        sharex=ax_joint
    )

    ax_marg_y = subfig.add_subplot(
        gs[1, 1],
        sharey=ax_joint
    )

    # ============================================================
    # JOINT
    # ============================================================

    # Joint gets the labels/numbers for the shared X and Y axes
    ax_joint.tick_params(
        axis='x',
        which='both',
        bottom=True,
        labelbottom=True
    )

    ax_joint.tick_params(
        axis='y',
        which='both',
        left=True,
        labelleft=True
    )


    # ============================================================
    # TOP MARGINAL
    # ============================================================

    # X is shared with joint:
    # KEEP ticks, REMOVE numbers
    ax_marg_x.tick_params(
        axis='x',
        which='both',
        bottom=True,
        labelbottom=False
    )

    # Y is its own density axis:
    # KEEP ticks AND numbers
    ax_marg_x.tick_params(
        axis='y',
        which='both',
        left=True,
        labelleft=True
    )


    # ============================================================
    # RIGHT MARGINAL
    # ============================================================

    # Y is shared with joint:
    # KEEP ticks, REMOVE numbers
    ax_marg_y.tick_params(
        axis='y',
        which='both',
        left=True,
        labelleft=False
    )

    # X is its own density axis:
    # KEEP ticks AND numbers
    ax_marg_y.tick_params(
        axis='x',
        which='both',
        bottom=True,
        labelbottom=True
    )
    ax_marg_x.spines['left'].set_visible(True)
    ax_marg_y.spines['bottom'].set_visible(True)
    # ax_marg_x.tick_params(axis='y', left=True, labelleft=True)
    # ax_marg_y.tick_params(axis='x', bottom=True, labelbottom=True)
    ax_marg_x.yaxis.label.set_visible(True)
    ax_marg_y.xaxis.label.set_visible(True)

    if density_labels:
        ax_marg_x.set_ylabel("Density")
        ax_marg_y.set_xlabel("Density")

    if cbar:
        pos = ax_marg_y.get_position()  # use ax_marg_y so cbar sits just right of it
        joint_pos = ax_joint.get_position()
        cbar_ax = subfig.add_axes([
            pos.x1 + 0.02,       # a bit to the right of ax_marg_y
            joint_pos.y0,        # bottom aligned with ax_joint
            0.03,                 # width
            joint_pos.height      # exact same height as ax_joint
        ])
        
        return ax_joint, ax_marg_x, ax_marg_y, cbar_ax
    
    return ax_joint, ax_marg_x, ax_marg_y

def plot_binned_line(x, y, bins, color, ax, label='',  stat='mean', spread='sem', min_count=5):
    import scipy.stats as ss

    x = np.asarray(x)
    y = np.asarray(y)

    bin_edges = np.linspace(np.nanmin(bins), np.nanmax(bins), len(bins))

    means, edges, _ = binned_statistic(x, y, statistic=stat, bins=bin_edges)
    counts, _, _    = binned_statistic(x, y, statistic='count', bins=bin_edges)
    stds, _, _      = binned_statistic(x, y, statistic='std', bins=bin_edges)

    centers = 0.5 * (edges[:-1] + edges[1:])

    if spread == 'sem':
        err = stds / np.sqrt(np.maximum(counts, 1))
    else:
        err = stds

    valid = counts >= min_count
    centers, means, err = centers[valid], means[valid], err[valid]

    if len(centers) < 2:
        return None, None, None

    ax.plot(centers, means, '-o', color=color, label=label, markersize=4)
    ax.fill_between(centers, means - err, means + err, color=color, alpha=0.25)

    # error-weighted regression
    weights = 1 / np.where(err > 0, err, np.nan)
    valid_w = ~np.isnan(weights)
    if valid_w.sum() >= 2:
        slope, intercept, r, p, _ = ss.linregress(
            centers[valid_w], means[valid_w])
        if p < 0.05 and abs(r) > 0:  # significant at 95%
            trend = slope * centers + intercept
            ax.plot(centers, trend, '--', color=color, linewidth=1.5)

    return centers, means, err

def add_map_features(ax): 
    ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3)
    
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="grey", alpha=0.6)
    gl.top_labels = gl.right_labels = gl.bottom_labels = gl.left_labels =  False

def diurnal_cycle_cmap(): 

    colors = [
    "#b61df0",  # purple
    "#0a1fc8",  # dark blue
    "#4285f0",  # blue
    "#8fd3e8",  # light blue
    "#00904a",  # dark green
    "#33ee00",  # bright green
    "#e6ee88",  # pale yellow-green
    "#eebb88",  # tan
    "#ffd800",  # yellow
    "#ff7800",  # orange
    "#d02814",  # red
    "#ff69b4",  # pink
    ]

    cmap = ListedColormap(colors)
    bounds = np.arange(0, 25, 2)
    norm = BoundaryNorm(bounds, cmap.N)

    return cmap, norm