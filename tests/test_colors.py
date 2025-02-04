"""
Test color and plotting functions -- warning, opens up many windows!
"""

import numpy as np
import pylab as pl
import sciris as sc
import pytest


#%% Functions

if 'doplot' not in locals():
    doplot = False
    sc.options(interactive=doplot)


def test_colors(doplot=doplot):
    sc.heading('Testing colors')
    o = sc.objdict()

    print('Testing shifthue')
    o.hue = sc.shifthue(colors=[(1,0,0),(0,1,0)], hueshift=0.5)

    print('Testing hex2rgb and rgb2hex')
    hx = '#87bc26'
    o.rgb = sc.hex2rgb(hx)
    o.hx = sc.rgb2hex(o.rgb)
    assert o.hx == hx

    print('Testing rgb2hsv and hsv2rgb')
    rgb = np.array([0.53, 0.74, 0.15])
    o.hsv = sc.rgb2hsv(rgb)
    o.rgb2 = sc.hsv2rgb(o.hsv)
    assert np.all(np.isclose(rgb, o.rgb2))
    
    print('Testing sanitizecolors')
    o.green1 = sc.sanitizecolor('g')
    o.green2 = sc.sanitizecolor('tab:green')
    o.crimson1 = sc.sanitizecolor('crimson')
    o.crimson2 = sc.sanitizecolor((220, 20, 60))
    assert o.crimson1 == o.crimson2
    o.midgrey = sc.sanitizecolor(0.5)
    with pytest.raises(ValueError):
        sc.sanitizecolor('not-a-color')

    return o


def test_colormaps(doplot=doplot):
    sc.heading('Testing colormaps')
    o = sc.objdict()

    print('Testing vectocolor')
    nanpos = 5
    nancolor = 'sienna'
    x = np.random.rand(10)
    x = sc.normalize(x) # To ensure the values span 0-1
    x[nanpos] = np.nan
    o.veccolors = sc.vectocolor(x, nancolor=nancolor, midpoint=0.3, cmap='turbo')
    assert (o.veccolors[nanpos,:] == sc.sanitizecolor(nancolor, asarray=True, alpha=1)).all()

    print('Testing arraycolors')
    n = 1000
    ncols = 5
    arr = pl.rand(n,ncols)
    for c in range(ncols):
        arr[:,c] += c
    x = pl.rand(n)
    y = pl.rand(n)
    colors = sc.arraycolors(arr)
    pl.figure('Array colors', figsize=(20,16))
    for c in range(ncols):
        pl.scatter(x+c, y, s=50, c=colors[:,c])
    o.arraycolors = colors

    print('Testing gridcolors')
    o.gridcolors = sc.gridcolors(ncolors=8,  demo=True)
    sc.gridcolors(ncolors=28, demo=True)
    print('\n8 colors:', o.gridcolors)

    print('Testing colormapdemo')
    sc.colormapdemo('parula', doshow=False)

    if not doplot:
        pl.close('all')

    return o


#%% Run as a script
if __name__ == '__main__':
    T = sc.timer()

    doplot = True
    sc.options(interactive=True)

    colors    = test_colors(doplot)
    colormaps = test_colormaps(doplot)

    if doplot:
        pl.show()

    T.toc()
    print('Done.')
