'''
Extensions to Matplotlib, including colormaps, 3D plotting, and plot manipulations.

Highlights:
    - ``sc.plot3d()``:c.surf3d() # easy way to render 3D plots
    - ``sc.boxoff()``: turn off top and right parts of the axes box
    - ``sc.commaticks()``: convert labels from "10000" and "1e6" to "10,000" and "1,000,0000"
    - ``sc.SIticks()``: convert labels from "10000" and "1e6" to "10k" and "1m"
    - ``sc.maximize()``: make the figure fill the whole screen
    - ``sc.savemovie()``: save a sequence of figures as an MP4 or other movie
    - ``sc.fonts()``: list available fonts or add new ones
'''

##############################################################################
#%% Imports
##############################################################################

import os
import warnings
import datetime as dt
import pylab as pl
import numpy as np
import matplotlib as mpl
import matplotlib.font_manager as mplfm
from . import sc_odict as sco
from . import sc_utils as scu
from . import sc_fileio as scf
from . import sc_printing as scp
from . import sc_datetime as scd


##############################################################################
#%% 3D plotting functions
##############################################################################

__all__ = ['fig3d', 'ax3d', 'plot3d', 'scatter3d', 'surf3d', 'bar3d']


def fig3d(returnax=False, figkwargs=None, axkwargs=None, **kwargs):
    '''
    Shortcut for creating a figure with 3D axes.

    Usually not invoked directly; kwargs are passed to figure()
    '''

    if figkwargs is None: figkwargs = {}
    if axkwargs is None: axkwargs = {}
    figkwargs.update(kwargs)

    fig,ax = ax3d(returnfig=True, figkwargs=figkwargs, **axkwargs)
    if returnax:
        return fig,ax
    else:
        return fig


def ax3d(fig=None, ax=None, returnfig=False, silent=False, elev=None, azim=None, figkwargs=None, axkwargs=None, **kwargs):
    '''
    Create a 3D axis to plot in.

    Usually not invoked directly; kwags are passed to add_subplot()
    '''
    from mpl_toolkits.mplot3d import Axes3D # analysis:ignore

    if figkwargs is None: figkwargs = {}
    if axkwargs is None: axkwargs = {}
    axkwargs.update(kwargs)
    nrows = axkwargs.pop('nrows', 1) # Since fig.add_subplot() can't handle kwargs...
    ncols = axkwargs.pop('ncols', 1)
    index = axkwargs.pop('index', 1)

    # Handle the figure
    if fig is None:
        if ax is None:
            fig = pl.figure(**figkwargs) # It's necessary to have an open figure or else the commands won't work
        else:
            fig = ax.figure
            silent = False
    else:
        silent = False # Never close an already open figure

    # Create and initialize the axis
    if ax is None:
        ax = fig.add_subplot(nrows, ncols, index, projection='3d', **axkwargs)
    if elev is not None or azim is not None:
        ax.view_init(elev=elev, azim=azim)
    if silent:
        pl.close(fig)
    if returnfig:
        return fig,ax
    else:
        return ax


def plot3d(x, y, z, c=None, fig=None, ax=None, returnfig=False, figkwargs=None, axkwargs=None, plotkwargs=None, **kwargs):
    '''
    Plot 3D data as a line

    Args:
        x (arr): x coordinate data
        y (arr): y coordinate data
        z (arr): z coordinate data
        fig (fig): an existing figure to draw the plot in
        ax (axes): an existing axes to draw the plot in
        returnfig (bool): whether to return the figure, or just the axes
        figkwargs (dict): passed to figure()
        axkwargs (dict): passed to axes()
        plotkwargs (dict): passed to plot()
        kwargs (dict): also passed to plot()

    **Example**::

        x,y,z = pl.rand(3,10)
        sc.plot3d(x, y, z)
    '''
    # Set default arguments
    plotkwargs = scu.mergedicts({'lw':2, 'c':c}, plotkwargs, kwargs)
    axkwargs = scu.mergedicts(axkwargs)

    # Create axis
    fig,ax = ax3d(returnfig=True, fig=fig, ax=ax, figkwargs=figkwargs, **axkwargs)

    ax.plot(x, y, z, **plotkwargs)

    if returnfig:
        return fig,ax
    else:
        return ax


def scatter3d(x, y, z, c=None, fig=None, returnfig=False, figkwargs=None, axkwargs=None, plotkwargs=None, **kwargs):
    '''
    Plot 3D data as a scatter

    Args:
        x (arr): x coordinate data
        y (arr): y coordinate data
        z (arr): z coordinate data
        c (arr): color data
        fig (fig): an existing figure to draw the plot in
        ax (axes): an existing axes to draw the plot in
        returnfig (bool): whether to return the figure, or just the axes
        figkwargs (dict): passed to figure()
        axkwargs (dict): passed to axes()
        plotkwargs (dict): passed to plot()
        kwargs (dict): also passed to plot()

    **Example**::

        x,y,z = pl.rand(3,10)
        sc.scatter3d(x, y, z, c=z)
    '''
    # Set default arguments
    plotkwargs = scu.mergedicts({'s':200, 'depthshade':False, 'linewidth':0}, plotkwargs, kwargs)
    axkwargs = scu.mergedicts(axkwargs)

    # Create figure
    fig,ax = ax3d(returnfig=True, fig=fig, figkwargs=figkwargs, **axkwargs)

    ax.scatter(x, y, z, c=c, **plotkwargs)

    if returnfig:
        return fig,ax
    else:
        return ax


def surf3d(data, x=None, y=None, fig=None, returnfig=False, colorbar=True, figkwargs=None, axkwargs=None, plotkwargs=None, **kwargs):
    '''
    Plot 2D data as a 3D surface

    Args:
        data (arr): 2D data
        x (arr): 1D vector or 2D grid of x coordinates (optional)
        y (arr): 1D vector or 2D grid of y coordinates (optional)
        fig (fig): an existing figure to draw the plot in
        ax (axes): an existing axes to draw the plot in
        returnfig (bool): whether to return the figure, or just the axes
        colorbar (bool): whether to plot a colorbar
        figkwargs (dict): passed to figure()
        axkwargs (dict): passed to axes()
        plotkwargs (dict): passed to plot()
        kwargs (dict): also passed to plot()

    **Example**::

        data = sc.smooth(pl.rand(30,50))
        sc.surf3d(data)
    '''

    # Set default arguments
    plotkwargs = scu.mergedicts({'cmap':'viridis'}, plotkwargs, kwargs)
    axkwargs = scu.mergedicts(axkwargs)

    # Create figure
    fig,ax = ax3d(returnfig=True, fig=fig, figkwargs=figkwargs, **axkwargs)
    ny,nx = pl.array(data).shape

    if x is None:
        x = np.arange(nx)
    if y is None:
        y = np.arange(ny)

    if x.ndim == 1 or y.ndim == 1:
        X,Y = np.meshgrid(x, y)
    else:
        X,Y = x,y

    surf = ax.plot_surface(X, Y, data, **plotkwargs)
    if colorbar:
        fig.colorbar(surf)

    if returnfig:
        return fig,ax
    else:
        return ax



def bar3d(data, fig=None, returnfig=False, cmap='viridis', figkwargs=None, axkwargs=None, plotkwargs=None, **kwargs):
    '''
    Plot 2D data as 3D bars

    Args:
        data (arr): 2D data
        fig (fig): an existing figure to draw the plot in
        ax (axes): an existing axes to draw the plot in
        returnfig (bool): whether to return the figure, or just the axes
        colorbar (bool): whether to plot a colorbar
        figkwargs (dict): passed to figure()
        axkwargs (dict): passed to axes()
        plotkwargs (dict): passed to plot()
        kwargs (dict): also passed to plot()

    **Example**::

        data = pl.rand(5,4)
        sc.bar3d(data)
    '''

    # Set default arguments
    plotkwargs = scu.mergedicts({'dx':0.8, 'dy':0.8, 'shade':True}, plotkwargs, kwargs)
    axkwargs = scu.mergedicts(axkwargs)

    # Create figure
    fig,ax = ax3d(returnfig=True, fig=fig, figkwargs=figkwargs, **axkwargs)

    x, y, z = [], [], []
    dz = []
    if 'color' not in plotkwargs:
        try:
            from . import sc_colors as scc # To avoid circular import
            plotkwargs['color'] = scc.vectocolor(data.flatten(), cmap=cmap)
        except Exception as E: # pragma: no cover
            print(f'bar3d(): Attempt to auto-generate colors failed: {str(E)}')
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            x.append(i)
            y.append(j)
            z.append(0)
            dz.append(data[i,j])
    ax.bar3d(x=x, y=y, z=z, dz=dz, **plotkwargs)

    if returnfig:
        return fig,ax
    else:
        return ax



##############################################################################
#%% Other plotting functions
##############################################################################

__all__ += ['boxoff', 'setaxislim', 'setxlim', 'setylim', 'commaticks', 'SIticks',
            'dateformatter', 'get_rows_cols', 'figlayout', 'maximize', 'fonts']


def boxoff(ax=None, removeticks=True, flipticks=True):
    '''
    Removes the top and right borders of a plot. Also optionally removes
    the tick marks, and flips the remaining ones outside.

    **Example**::

        pl.plot([2,5,3])
        sc.boxoff()

    Version: 2017may22
    '''
    from pylab import gca
    if ax is None: ax = gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if removeticks:
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
    if flipticks:
        ax.tick_params(direction='out', pad=5)
    return ax



def setaxislim(which=None, ax=None, data=None):
    '''
    A small script to determine how the y limits should be set. Looks
    at all data (a list of arrays) and computes the lower limit to
    use, e.g.::

        sc.setaxislim([np.array([-3,4]), np.array([6,4,6])], ax)

    will keep Matplotlib's lower limit, since at least one data value
    is below 0.

    Note, if you just want to set the lower limit, you can do that
    with this function via::

        sc.setaxislim()
    '''

    # Handle which axis
    if which is None:
        which = 'both'
    if which not in ['x','y','both']:
        errormsg = f'Setting axis limit for axis {which} is not supported'
        raise ValueError(errormsg)
    if which == 'both':
        setaxislim(which='x', ax=ax, data=data)
        setaxislim(which='y', ax=ax, data=data)
        return None

    # Ensure axis exists
    if ax is None:
        ax = pl.gca()

    # Get current limits
    if   which == 'x': currlower, currupper = ax.get_xlim()
    elif which == 'y': currlower, currupper = ax.get_ylim()

    # Calculate the lower limit based on all the data
    lowerlim = 0
    upperlim = 0
    if scu.checktype(data, 'arraylike'): # Ensure it's numeric data (probably just None)
        flatdata = scu.promotetoarray(data).flatten() # Make sure it's iterable
        lowerlim = min(lowerlim, flatdata.min())
        upperlim = max(upperlim, flatdata.max())

    # Set the new y limits
    if lowerlim<0: lowerlim = currlower # If and only if the data lower limit is negative, use the plotting lower limit
    upperlim = max(upperlim, currupper) # Shouldn't be an issue, but just in case...

    # Specify the new limits and return
    if   which == 'x': ax.set_xlim((lowerlim, upperlim))
    elif which == 'y': ax.set_ylim((lowerlim, upperlim))
    return lowerlim,upperlim


def setxlim(data=None, ax=None):
    ''' Alias for sc.setaxislim(which='x') '''
    return setaxislim(data=data, ax=ax, which='x')


def setylim(data=None, ax=None):
    '''
    Alias for sc.setaxislim(which='y').

    **Example**::

        pl.plot([124,146,127])
        sc.setylim() # Equivalent to pl.ylim(bottom=0)
    '''
    return setaxislim(data=data, ax=ax, which='y')


def _get_axlist(ax):
    ''' Helper function to turn either a figure, an axes, or a list of axes into a list of axes '''

    if ax is None: # If not supplied, get current axes
        axlist = [pl.gca()]
    elif isinstance(ax, pl.Axes): # If it's an axes, turn to a list
        axlist = [ax]
    elif isinstance(ax, pl.Figure): # If it's a figure, pull all axes
        axlist = ax.axes
    elif isinstance(ax, list): # If it's a list, use directly
        axlist = ax
    else:
        errormsg = f'Could not recognize object {type(ax)}: must be None, Axes, Figure, or list of axes'
        raise ValueError(errormsg)

    return axlist


def commaticks(ax=None, axis='y'):
    '''
    Use commas in formatting the y axis of a figure (e.g., 34,000 instead of 34000)

    Args:
        ax (any): axes to modify; if None, use current; else can be a single axes object, a figure, or a list of axes
        axis (str): which axes to change (default 'y')

    **Example**::

        data = pl.rand(10)*1e4
        pl.plot(data)
        sc.commaticks()

    See http://stackoverflow.com/questions/25973581/how-to-format-axis-number-format-to-thousands-with-a-comma-in-matplotlib
    '''
    def commaformatter(x, pos=None):
        string = f'{x:,}' # Do the formatting
        if string[-2:] == '.0': # Trim the end, if it's a float but should be an int
            string = string[:-2]
        return string

    axlist = _get_axlist(ax)
    for ax in axlist:
        if   axis=='x': thisaxis = ax.xaxis
        elif axis=='y': thisaxis = ax.yaxis
        elif axis=='z': thisaxis = ax.zaxis
        else: raise ValueError('Axis must be x, y, or z')
        thisaxis.set_major_formatter(mpl.ticker.FuncFormatter(commaformatter))
    return None



def SIticks(ax=None, axis='y', fixed=False):
    '''
    Apply SI tick formatting to one axis of a figure  (e.g., 34k instead of 34000)

    Args:
        ax (any): axes to modify; if None, use current; else can be a single axes object, a figure, or a list of axes
        axis (str): which axes to change (default 'y')
        fixed (bool): use fixed-location tick labels (by default, update them dynamically)

    **Example**::

        data = pl.rand(10)*1e4
        pl.plot(data)
        sc.SIticks()
    '''
    def SItickformatter(x, pos=None, sigfigs=2, SI=True, *args, **kwargs):  # formatter function takes tick label and tick position
        ''' Formats axis ticks so that e.g. 34000 becomes 34k -- usually not invoked directly '''
        output = scp.sigfig(x, sigfigs=sigfigs, SI=SI) # Pretty simple since scp.sigfig() does all the work
        return output

    axlist = _get_axlist(ax)
    for ax in axlist:
        if   axis=='x': thisaxis = ax.xaxis
        elif axis=='y': thisaxis = ax.yaxis
        elif axis=='z': thisaxis = ax.zaxis
        else: raise ValueError('Axis must be x, y, or z')
        if fixed:
            ticklocs = thisaxis.get_ticklocs()
            ticklabels = []
            for tickloc in ticklocs:
                ticklabels.append(SItickformatter(tickloc))
            thisaxis.set_major_formatter(mpl.ticker.FixedFormatter(ticklabels))
        else:
            thisaxis.set_major_formatter(mpl.ticker.FuncFormatter(SItickformatter))
    return None



def dateformatter(start_date=None, dateformat=None, interval=None, start=None, end=None, rotation=None, ax=None, **kwargs):
    '''
    Create an automatic date formatter based on a number of days and a start day.

    Wrapper for Matplotlib's date formatter. Note, start_date is not required if the
    axis uses dates already (otherwise, the mapping will follow Matplotlib's default,
    i.e. 0 = 1970-01-01). Note: this function is intended to work on the x-axis only.

    Args:
        start_date (str/date): the start day, either as a string or date object; if none is supplied, treat current data as a date
        dateformat (str): the date format (default '%Y-%b-%d')
        interval (int): if supplied, the interval between ticks (must supply an axis also to take effect)
        start (str/int): if supplied, the lower limit of the axis
        end (str/int): if supplied, the upper limit of the axis
        rotation (float): rotation of the labels, in degrees
        ax (axes): if supplied, automatically set the x-axis formatter for this axis

    **Examples**::

        # Automatically configure the axis with default options
        pl.plot(np.arange(365), pl.rand(365))
        sc.dateformatter('2021-01-01')

        # Manually configure
        ax = pl.subplot(111)
        ax.plot(np.arange(60), np.random.random(60))
        formatter = sc.dateformatter(start_date='2020-04-04', interval=7, start='2020-05-01', end=50, dateformat='%m-%d', ax=ax)
        ax.xaxis.set_major_formatter(formatter)

    New in version 1.2.0.
    New in version 1.2.2: "rotation" argument; renamed "start_day" to "start_date"
    '''

    # Handle deprecation
    start_day = kwargs.pop('start_day', None)
    if start_day is not None: # pragma: no cover
        start_date = start_day
        warnmsg = 'sc.dateformatter() argument "start_day" has been deprecated as of v1.2.2; use "start_date" instead'
        warnings.warn(warnmsg, category=DeprecationWarning, stacklevel=2)

    # Handle axis
    if ax is None:
        ax = pl.gca()

    # Set the default format -- "2021-01-01"
    if dateformat is None:
        dateformat = '%Y-%m-%d'

    # Convert to a date object
    if start_date is None:
        start_date = pl.num2date(ax.dataLim.x0)
    start_date = scd.date(start_date)

    @mpl.ticker.FuncFormatter
    def mpl_formatter(x, pos):
        return (start_date + dt.timedelta(days=int(x))).strftime(dateformat)

    # Handle limits
    xmin, xmax = ax.get_xlim()
    if start:
        xmin = scd.day(start, start_date=start_date)
    if end:
        xmax = scd.day(end, start_date=start_date)
    ax.set_xlim((xmin, xmax))

    # Set the x-axis intervals
    if interval:
        ax.set_xticks(np.arange(xmin, xmax+1, interval))

    # Set the rotation
    if rotation:
        ax.tick_params(axis='x', labelrotation=rotation)

    # Set the formatter
    ax.xaxis.set_major_formatter(mpl_formatter)

    return mpl_formatter



def get_rows_cols(n, nrows=None, ncols=None, ratio=1, make=False, tight=True, remove_extra=True, **kwargs):
    '''
    If you have 37 plots, then how many rows and columns of axes do you know? This
    function convert a number (i.e. of plots) to a number of required rows and columns.
    If nrows or ncols is provided, the other will be calculated. Ties are broken
    in favor of more rows (i.e. 7x6 is preferred to 6x7). It can also generate
    the plots, if make=True.

    Args:
        n (int): the number (of plots) to accommodate
        nrows (int): if supplied, keep this fixed and calculate the columns
        ncols (int): if supplied, keep this fixed and calculate the rows
        ratio (float): sets the number of rows relative to the number of columns (i.e. for 100 plots, 1 will give 10x10, 4 will give 20x5, etc.).
        make (bool): if True, generate subplots
        tight (bool): if True and make is True, then apply tight layout
        remove_extra (bool): if True and make is True, then remove extra subplots
        kwargs (dict): passed to pl.subplots()

    Returns:
        A tuple of ints for the number of rows and the number of columns (which, of course, you can reverse)

    **Examples**::

        nrows,ncols = sc.get_rows_cols(36) # Returns 6,6
        nrows,ncols = sc.get_rows_cols(37) # Returns 7,6
        nrows,ncols = sc.get_rows_cols(100, ratio=2) # Returns 15,7
        nrows,ncols = sc.get_rows_cols(100, ratio=0.5) # Returns 8,13 since rows are prioritized
        fig,axs     = sc.get_rows_cols(37, make=True) # Create 7x6 subplots

    New in version 1.0.0.
    New in version 1.2.0: "make", "tight", and "remove_extra" arguments
    '''

    # Simple cases -- calculate the one missing
    if nrows is not None:
        ncols = int(np.ceil(n/nrows))
    elif ncols is not None:
        nrows = int(np.ceil(n/ncols))

    # Standard case -- calculate both
    else:
        guess = np.sqrt(n)
        nrows = int(np.ceil(guess*np.sqrt(ratio)))
        ncols = int(np.ceil(n/nrows)) # Could also call recursively!

    # If asked, make subplots
    if make:
        fig, axs = pl.subplots(nrows=nrows, ncols=ncols, **kwargs)
        if remove_extra:
            for ax in axs.flat[n:]:
                ax.set_visible(False) # to remove last plot
        if tight:
            figlayout(fig, tight=True)
        return fig,axs
    else: # Otherwise, just return rows and columns
        return nrows,ncols

getrowscols = get_rows_cols # Alias


def figlayout(fig=None, tight=True, keep=False, **kwargs):
    '''
    Alias to both fig.set_tight_layout() and fig.subplots_adjust().

    Args:
        fig (Figure): the figure (by default, use current)
        tight (bool, or dict): passed to fig.set_tight_layout(); default True
        keep (bool): if True, then leave tight layout on; else, turn it back off
        kwargs (dict): passed to fig.subplots_adjust()

    **Example**::

        fig,axs = sc.get_rows_cols(37, make=True, tight=False) # Create 7x6 subplots, squished together
        sc.figlayout(bottom=0.3)

    New in version 1.2.0.
    '''
    if isinstance(fig, bool):
        fig = None
        tight = fig # To allow e.g. sc.figlayout(False)
    if fig is None:
        fig = pl.gcf()
    fig.set_tight_layout(tight)
    if not keep:
        pl.pause(0.01) # Force refresh
        fig.set_tight_layout(False)
    if len(kwargs):
        fig.subplots_adjust(**kwargs)
    return


def maximize(fig=None, die=False):  # pragma: no cover
    '''
    Maximize the current (or supplied) figure. Note: not guaranteed to work for
    all Matplotlib backends (e.g., agg).

    Args:
        fig (Figure): the figure object; if not supplied, use the current active figure
        die (bool): whether to propagate an exception if encountered (default no)

    **Example**::

        pl.plot([2,3,5])
        sc.maximize()

    New in version 1.0.0.
    '''
    backend = pl.get_backend().lower()
    if fig is not None:
        pl.figure(fig.number) # Set the current figure
    try:
        mgr = pl.get_current_fig_manager()
        if   'qt'  in backend: mgr.window.showMaximized()
        elif 'gtk' in backend: mgr.window.maximize()
        elif 'wx'  in backend: mgr.frame.Maximize(True)
        elif 'tk'  in backend: mgr.resize(*mgr.window.maxsize())
        else:
            errormsg = f'The maximize() function is not supported for the backend "{backend}"; use Qt5Agg if possible'
            raise NotImplementedError(errormsg)
    except Exception as E:
        errormsg = f'Warning: maximizing the figure failed because: "{str(E)}"'
        if die:
            raise RuntimeError(errormsg) from E
        else:
            print(errormsg)
    return


def fonts(add=None, use=False, **kwargs):
    '''
    List available fonts, or add new ones. Alias to Matplotlib's font manager.

    Args:
        add (str/list): path of the fonts or folders to add; if none, list available fonts
        use (bool): set the last-added font as the default font (default: false)
        kwargs (dict): passed to matplotlib.font_manager.findSystemFonts()

    **Examples**::

        sc.fonts() # List available fonts
        sc.fonts('myfont.ttf', use=True) # Add this font and immediately set to default
        sc.fonts(['/folder1', '/folder2']) # Add all fonts in both folders
    '''

    if add is None:
        available_fonts = []
        for f in mplfm.findSystemFonts(**kwargs):
            try:
                name = mplfm.get_font(f).family_name
                available_fonts.append(name)
            except:
                pass
        available_fonts = np.unique(available_fonts).tolist()
        return available_fonts

    else:
        paths = scu.promotetolist(add)
        for font in mplfm.findSystemFonts(paths, **kwargs):
            mplfm.fontManager.addfont(font)
        if use: # Set as default font
            pl.rc('font', family=font.family_name)

    return


##############################################################################
#%% Figure saving
##############################################################################

__all__ += ['savefigs', 'loadfig', 'emptyfig', 'separatelegend', 'orderlegend', 'savemovie']


def savefigs(figs=None, filetype=None, filename=None, folder=None, savefigargs=None, aslist=False, verbose=False, **kwargs):
    '''
    Save the requested plots to disk.

    Args:
        figs:        the figure objects to save
        filetype:    the file type; can be 'fig', 'singlepdf' (default), or anything supported by savefig()
        filename:    the file to save to (only uses path if multiple files)
        folder:      the folder to save the file(s) in
        savefigargs: dictionary of arguments passed to savefig()
        aslist:      whether or not return a list even for a single file

    **Examples**::

        import pylab as pl
        import sciris as sc
        fig1 = pl.figure(); pl.plot(pl.rand(10))
        fig2 = pl.figure(); pl.plot(pl.rand(10))
        sc.savefigs([fig1, fig2]) # Save everything to one PDF file
        sc.savefigs(fig2, 'png', filename='myfig.png', savefigargs={'dpi':200})
        sc.savefigs([fig1, fig2], filepath='/home/me', filetype='svg')
        sc.savefigs(fig1, position=[0.3,0.3,0.5,0.5])

    If saved as 'fig', then can load and display the plot using sc.loadfig().

    Version: 2018aug26
    '''

    # Preliminaries
    wasinteractive = pl.isinteractive() # You might think you can get rid of this...you can't!
    if wasinteractive: pl.ioff()
    if filetype is None: filetype = 'singlepdf' # This ensures that only one file is created

    # Either take supplied plots, or generate them
    figs = sco.odict.promote(figs)
    nfigs = len(figs)

    # Handle file types
    filenames = []
    if filetype=='singlepdf': # See http://matplotlib.org/examples/pylab_examples/multipage_pdf.html
        from matplotlib.backends.backend_pdf import PdfPages
        defaultname = 'figures.pdf'
        fullpath = scf.makefilepath(filename=filename, folder=folder, default=defaultname, ext='pdf')
        pdf = PdfPages(fullpath)
        filenames.append(fullpath)
        if verbose: print(f'PDF saved to {fullpath}')
    for p,item in enumerate(figs.items()):
        key,plt = item
        # Handle filename
        if filename and nfigs==1: # Single plot, filename supplied -- use it
            fullpath = scf.makefilepath(filename=filename, folder=folder, default='Figure', ext=filetype) # NB, this filename not used for singlepdf filetype, so it's OK
        else: # Any other case, generate a filename
            keyforfilename = filter(str.isalnum, str(key)) # Strip out non-alphanumeric stuff for key
            defaultname = keyforfilename
            fullpath = scf.makefilepath(filename=filename, folder=folder, default=defaultname, ext=filetype)

        # Do the saving
        if savefigargs is None: savefigargs = {}
        defaultsavefigargs = {'dpi':200, 'bbox_inches':'tight'} # Specify a higher default DPI and save the figure tightly
        defaultsavefigargs.update(savefigargs) # Update the default arguments with the user-supplied arguments
        if filetype == 'fig':
            scf.saveobj(fullpath, plt)
            filenames.append(fullpath)
            if verbose: print(f'Figure object saved to {fullpath}')
        else:
            reanimateplots(plt)
            if filetype=='singlepdf':
                pdf.savefig(figure=plt, **defaultsavefigargs) # It's confusing, but defaultsavefigargs is correct, since we updated it from the user version
            else:
                plt.savefig(fullpath, **defaultsavefigargs)
                filenames.append(fullpath)
                if verbose: print(f'{filetype.upper()} plot saved to {fullpath}')
            pl.close(plt)

    # Do final tidying
    if filetype=='singlepdf': pdf.close()
    if wasinteractive: pl.ion()
    if aslist or len(filenames)>1:
        return filenames
    else:
        return filenames[0]


def loadfig(filename=None):
    '''
    Load a plot from a file and reanimate it.

    **Example usage**::

        import pylab as pl
        import sciris as sc
        fig = pl.figure(); pl.plot(pl.rand(10))
        sc.savefigs(fig, filetype='fig', filename='example.fig')

    **Later**::

        example = sc.loadfig('example.fig')
    '''
    pl.ion() # Without this, it doesn't show up
    fig = scf.loadobj(filename)
    reanimateplots(fig)
    return fig


def reanimateplots(plots=None):
    ''' Reconnect plots (actually figures) to the Matplotlib backend. Plots must be an odict of figure objects. '''
    try:
        from matplotlib.backends.backend_agg import new_figure_manager_given_figure as nfmgf # Warning -- assumes user has agg on their system, but should be ok. Use agg since doesn't require an X server
    except Exception as E: # pragma: no cover
        errormsg = f'To reanimate plots requires the "agg" backend, which could not be imported: {repr(E)}'
        raise ImportError(errormsg) from E
    if len(pl.get_fignums()): fignum = pl.gcf().number # This is the number of the current active figure, if it exists
    else: fignum = 1
    plots = sco.odict.promote(plots) # Convert to an odict
    for plot in plots.values(): nfmgf(fignum, plot) # Make sure each figure object is associated with the figure manager -- WARNING, is it correct to associate the plot with an existing figure?
    return None


def emptyfig():
    ''' The emptiest figure possible '''
    fig = pl.Figure(facecolor='None')
    return fig


def _get_legend_handles(ax, handles, labels):
    '''
    Construct handle and label list, from one of:
     - A list of handles and a list of labels
     - A list of handles, where each handle contains the label
     - An axis object, containing the objects that should appear in the legend
     - A figure object, from which the first axis will be used
    '''
    if handles is None:
        if ax is None:
            ax = pl.gca()
        elif isinstance(ax, pl.Figure): # Allows an argument of a figure instead of an axes
            ax = ax.axes[-1]
        handles, labels = ax.get_legend_handles_labels()
    else:
        if labels is None:
            labels = [h.get_label() for h in handles]
        else:
            assert len(handles) == len(labels), f"Number of handles ({len(handles)}) and labels ({len(labels)}) must match"
    return ax, handles, labels


def separatelegend(ax=None, handles=None, labels=None, reverse=False, figsettings=None, legendsettings=None):
    ''' Allows the legend of a figure to be rendered in a separate window instead '''

    # Handle settings
    f_settings = scu.mergedicts({'figsize':(4.0,4.8)}, figsettings) # (6.4,4.8) is the default, so make it a bit narrower
    l_settings = scu.mergedicts({'loc': 'center', 'bbox_to_anchor': None, 'frameon': False}, legendsettings)

    # Get handles and labels
    _, handles, labels = _get_legend_handles(ax, handles, labels)

    # Set up new plot
    fig = pl.figure(**f_settings)
    ax = fig.add_subplot(111)
    ax.set_position([-0.05,-0.05,1.1,1.1]) # This cuts off the axis labels, ha-ha
    ax.set_axis_off()  # Hide axis lines

    # A legend renders the line/patch based on the object handle. However, an object
    # can only appear in one figure. Thus, if the legend is in a different figure, the
    # object cannot be shown in both the original figure and in the legend. Thus we need
    # to copy the handles, and use the copies to render the legend
    handles2 = []
    for h in handles:
        h2 = scu.cp(h)
        h2.axes = None
        h2.figure = None
        handles2.append(h2)

    # Reverse order, e.g. for stacked plots
    if reverse:
        handles2 = handles2[::-1]
        labels   = labels[::-1]

    # Plot the new legend
    ax.legend(handles=handles2, labels=labels, **l_settings)

    return fig


def orderlegend(order=None, ax=None, handles=None, labels=None, reverse=None, **kwargs):
    '''
    Create a legend with a specified order, or change the order of an existing legend.
    Can either specify an order, or use the reverse argument to simply reverse the order.
    Note: you do not need to create the legend before calling this function; if you do,
    you will need to pass any additional keyword arguments to this function since it will
    override existing settings.

    Args:
        order (list or array): the new order of the legend, as from e.g. np.argsort()
        ax (axes): the axes object; if omitted, defaults to current axes
        handles (list): the legend handles; can be used instead of ax
        labels (list): the legend labels; can be used instead of ax
        reverse (bool): if supplied, simply reverse the legend order
        kwargs (dict): passed to ax.legend()

    **Examples**::

        pl.plot([1,4,3], label='A')
        pl.plot([5,7,8], label='B')
        pl.plot([2,5,2], label='C')
        sc.orderlegend(reverse=True) # Legend order C, B, A
        sc.orderlegend([1,0,2], frameon=False) # Legend order B, A, C with no frame
        pl.legend() # Restore original legend order A, B, C
    '''

    # Get handles and labels
    ax, handles, labels = _get_legend_handles(ax, handles, labels)
    if order:
        handles = [handles[o] for o in order]
        labels = [labels[o] for o in order]
    if reverse:
        handles = handles[::-1]
        labels = labels[::-1]

    ax.legend(handles, labels, **kwargs)

    return

def savemovie(frames, filename=None, fps=None, quality=None, dpi=None, writer=None, bitrate=None, interval=None, repeat=False, repeat_delay=None, blit=False, verbose=True, **kwargs):
    '''
    Save a set of Matplotlib artists as a movie.

    Args:
        frames (list): The list of frames to animate
        filename (str): The name (or full path) of the file; expected to end with mp4 or gif (default movie.mp4)
        fps (int): The number of frames per second (default 10)
        quality (string): The quality of the movie, in terms of dpi (default "high" = 300 dpi)
        dpi (int): Instead of using quality, set an exact dpi
        writer (str or object): Specify the writer to be passed to matplotlib.animation.save() (default "ffmpeg")
        bitrate (int): The bitrate. Note, may be ignored; best to specify in a writer and to pass in the writer as an argument
        interval (int): The interval between frames; alternative to using fps
        repeat (bool): Whether or not to loop the animation (default False)
        repeat_delay (bool): Delay between repeats, if repeat=True (default None)
        blit (bool): Whether or not to "blit" the frames (default False, since otherwise does not detect changes )
        verbose (bool): Whether to print statistics on finishing.
        kwargs (dict): Passed to matplotlib.animation.save()

    Returns:
        A Matplotlib animation object

    **Examples**::

        import pylab as pl
        import sciris as sc

        # Simple example (takes ~5 s)
        frames = [pl.plot(pl.cumsum(pl.randn(100))) for i in range(20)] # Create frames
        sc.savemovie(frames, 'dancing_lines.gif') # Save movie as medium-quality gif

        # Complicated example (takes ~15 s)
        nframes = 100 # Set the number of frames
        ndots = 100 # Set the number of dots
        axislim = 5*pl.sqrt(nframes) # Pick axis limits
        dots = pl.zeros((ndots, 2)) # Initialize the dots
        frames = [] # Initialize the frames
        old_dots = sc.dcp(dots) # Copy the dots we just made
        fig = pl.figure(figsize=(10,8)) # Create a new figure
        for i in range(nframes): # Loop over the frames
            dots += pl.randn(ndots, 2) # Move the dots randomly
            color = pl.norm(dots, axis=1) # Set the dot color
            old = pl.array(old_dots) # Turn into an array
            plot1 = pl.scatter(old[:,0], old[:,1], c='k') # Plot old dots in black
            plot2 = pl.scatter(dots[:,0], dots[:,1], c=color) # Note: Frames will be separate in the animation
            pl.xlim((-axislim, axislim)) # Set x-axis limits
            pl.ylim((-axislim, axislim)) # Set y-axis limits
            kwargs = {'transform':pl.gca().transAxes, 'horizontalalignment':'center'} # Set the "title" properties
            title = pl.text(0.5, 1.05, f'Iteration {i+1}/{nframes}', **kwargs) # Unfortunately pl.title() can't be dynamically updated
            pl.xlabel('Latitude') # But static labels are fine
            pl.ylabel('Longitude') # Ditto
            frames.append((plot1, plot2, title)) # Store updated artists
            old_dots = pl.vstack([old_dots, dots]) # Store the new dots as old dots
        sc.savemovie(frames, 'fleeing_dots.mp4', fps=20, quality='high') # Save movie as a high-quality mp4

    Version: 2019aug21
    '''

    from matplotlib import animation # Place here since specific only to this function

    if not isinstance(frames, list):
        errormsg = f'sc.savemovie(): argument "frames" must be a list, not "{type(frames)}"'
        raise TypeError(errormsg)
    for f in range(len(frames)):
        if not scu.isiterable(frames[f]):
            frames[f] = (frames[f],) # This must be either a tuple or a list to work with ArtistAnimation

    # Try to get the figure from the frames, else use the current one
    try:    fig = frames[0][0].get_figure()
    except: fig = pl.gcf()

    # Set parameters
    if filename is None:
        filename = 'movie.mp4'
    if writer is None:
        if   filename.endswith('mp4'): writer = 'ffmpeg'
        elif filename.endswith('gif'): writer = 'imagemagick'
        else:
            errormsg = f'sc.savemovie(): unknown movie extension for file {filename}'
            raise ValueError(errormsg)
    if fps is None:
        fps = 10
    if interval is None:
        interval = 1000./fps
        fps = 1000./interval # To ensure it's correct

    # Handle dpi/quality
    if dpi is None and quality is None:
        quality = 'medium' # Make it medium quailty by default
    if isinstance(dpi, str):
        quality = dpi # Interpret dpi arg as a quality command
        dpi = None
    if dpi is not None and quality is not None:
        print(f'sc.savemovie() warning: quality is simply a shortcut for dpi; please specify one or the other, not both (dpi={dpi}, quality={quality})')
    if quality is not None:
        if   quality == 'low':    dpi =  50
        elif quality == 'medium': dpi = 150
        elif quality == 'high':   dpi = 300
        else:
            errormsg = f'Quality must be high, medium, or low, not "{quality}"'
            raise ValueError(errormsg)

    # Optionally print progress
    if verbose:
        start = scd.tic()
        print(f'Saving {len(frames)} frames at {fps} fps and {dpi} dpi to "{filename}" using {writer}...')

    # Actually create the animation -- warning, no way to not actually have it render!
    anim = animation.ArtistAnimation(fig, frames, interval=interval, repeat_delay=repeat_delay, repeat=repeat, blit=blit)
    anim.save(filename, writer=writer, fps=fps, dpi=dpi, bitrate=bitrate, **kwargs)

    if verbose:
        print(f'Done; movie saved to "{filename}"')
        try: # Not essential, so don't try too hard if this doesn't work
            filesize = os.path.getsize(filename)
            if filesize<1e6: print(f'File size: {filesize/1e3:0.0f} KB')
            else:            print(f'File size: {filesize/1e6:0.2f} MB')
        except:
            pass
        scd.toc(start)

    return anim