#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.

import os
import sys
import random
import time
from threading import Thread

# for now, nothing here is intended to be installed or `pip`able.
# Fixup the system path to add in ./src so the imports work.
#
from os.path import abspath, dirname
sys.path.insert(0, abspath(dirname(__file__)) + os.sep + 'src')

import zwi
from zwi import ZwiPro, debug, verbo, get_zdir

# XXXXXXXXXXXXXx
# This is just madly hacked together so as to figure out minimal Bokeh to
# get something working.
# A massive restructure/rewrite is due soon.
# XXXXXXXXXXXXXx
#
# There is some flask stuff I cut&pasted which currently does nothing.
#
try:
    import bokeh
    from bokeh.io import curdoc
    from bokeh.models import ColumnDataSource, Slider, TextInput, Dropdown, Select, Toggle, HoverTool
    from bokeh.models import CDSView, GroupFilter, BooleanFilter, IndexFilter
    from bokeh.models import Button
    from bokeh.models.glyphs import Text, Rect
    from bokeh.models.annotations import Title
    from bokeh.layouts import column, row
    from bokeh.plotting import figure, show, output_notebook
    from bokeh.events import ButtonClick
    from bokeh.server.server import Server
    from bokeh.application import Application
    from bokeh.application.handlers.function import FunctionHandler
    from tornado.ioloop import IOLoop

    from collections import OrderedDict
    import flask
    import pandas as pd
    import numpy as np
except Exception as e:
    print('import error', e)
    raise SystemExit('use `pip3 install` to install missing modules.')


class ZwiBok(object):
    plot_data = []
    last_data_length = None

    def __init__(self):
        thread = Thread(target=self.startDataAcquisition)
        thread.start()

        io_loop = IOLoop.current()
        server = Server(applications=
                        {
                            '/myapp': Application(FunctionHandler(self.make_document))
                        },
                        io_loop=io_loop, port=5001
        )
        server.start()
        server.show('/myapp')
        io_loop.start()

    def startDataAcquisition(self):
        while True:
            self.plot_data.append({
                'x': [random.random()],
                'y': [random.random()],
                'color': [random.choice(['red', 'blue', 'green'])]})
            time.sleep(5)

    def make_document(self, doc):
        source = ColumnDataSource({'x': [], 'y': [], 'color': []})
        fig = figure(title='Streaming Circle Plot!', sizing_mode='scale_both')
        fig.circle(source=source, x='x', y='y', color='color', size=10)

        def update():
            if self.last_data_length is not None and self.last_data_length != len(self.plot_data):
                source.stream(self.plot_data[-1])
            self.last_data_length = len(self.plot_data)

        doc.add_root(fig)
        doc.add_periodic_callback(update, 1000)


# app = BokehApp()

# curdoc().theme = "dark_minimal"
pro = ZwiPro()
which = 'age'
icol = [
    'id',
    'age', 'height', 'weight', 'ftp',
    'achievementLevel',
    'totalDistance',
    'totalDistanceClimbed',
    'totalTimeInMinutes',
    'totalWattHours',
    'totalExperiencePoints',
    'totalGold',
]
col = [
    'firstName', 'lastName',
    'male',
    'imageSrc',
    'playerType',
    'countryAlpha3',
] + icol

COL_WIDTH = 200
ROW_HEIGHT = 48
CIRCLE_ALPHA = 0.7

# Set up widgets
text = TextInput(title='title', value=f'{which} plot', width=2*COL_WIDTH, height=ROW_HEIGHT)
x_sel = Select(value='age', title='X', options=icol, width=COL_WIDTH, height=ROW_HEIGHT)
y_sel = Select(value='ftp', title='Y', options=icol, width=COL_WIDTH, height=ROW_HEIGHT)
reset = Button(label='reset', width=COL_WIDTH, height=ROW_HEIGHT)
radius = Slider(title='radius', value=10, start=1, end=20, step=1, width=COL_WIDTH, height=ROW_HEIGHT)
do_male = Toggle(label='male', active=True, width=COL_WIDTH, height=ROW_HEIGHT)
do_fema = Toggle(label='female', active=True, width=COL_WIDTH, height=ROW_HEIGHT)
buto = row(do_male, do_fema, width=2*COL_WIDTH, height=ROW_HEIGHT)

def ic_callback(cache):
    debug(1, f'callback: {cache=}')

    def process(wrk):
        pass

    cache.update(process)
    pass
    
#
# attach the asset cache for the images
#
icache = zwi.AssetCache(get_zdir('.image-cache'), ic_callback)

# XXXXXXXXXXXXXXXXXXXXXXXXX
# This does not work. I need to run a local WEB server to
# serve these files.
# XXXXXXXXXXXXXXXXXXXXXXXXX
def ic_lookup(url, df):
    rv = icache.load(url, df)
    if rv is None:
        return url
    return 'file://' + rv

def pro_to_df(pro, want):
    """Subset and convert from ZwiPro() to DataFrame()."""
    res = {c: [] for c in want}
            
    for r in pro._pro:	# iterate over rows
        if int(r[pro.cols.index('weight')]) // 1000 > 500:
            continue	# >500kg?
        if int(r[pro.cols.index('totalDistance')]) // 1000 == 0:
            continue	# skip those with zero total distance
        if int(r[pro.cols.index('totalTimeInMinutes')]) == 0:
            continue	# skip those with zero total distance
        
        for c in want:	# iterate over the desired columns
            res[c].append(r[pro.cols.index(c)])
            pass
        pass

    return pd.DataFrame(res)

df = pro_to_df(pro, col)
# debug(2, df)
# debug(2, df.query('20 <= age and age < 21'))
#
# adjust some values
#
def minmax(x, mi, ma):
    if x < mi:
        return mi
    if x > ma:
        return ma
    return x

df['age'] = df['age'].apply(lambda x: minmax(x, 0, 120))
df['ftp'] = df['ftp'].apply(lambda x: minmax(x, 0, 2000))
df['achievementLevel'] = df['achievementLevel'].apply(lambda x: int(x) // 100)
df['weight'] = df['weight'].apply(lambda x: int(x) // 1000)
df['height'] = df['height'].apply(lambda x: int(x) // 10)
df['totalDistance'] = df['totalDistance'].apply(lambda x: int(x) // 1000)
if False:
    # XXXXXXXx not working yet
    df['imageSrc'] = df['imageSrc'].apply(lambda x: ic_lookup(x, df))
    print(df['imageSrc'])
    pass

NONE = 'https://upload.wikimedia.org/wikipedia/commons/c/ce/Image_of_none.svg'

def map_none(x):
    if x is None or x == 'None':
        return NONE
    else:
        return x
    pass

df['imageSrc'] = df['imageSrc'].apply(lambda x: map_none(x))
print(df['imageSrc'])
pass


sliders = {}
# Set up layouts and add to document
inputs = column(text,
                buto,
                row(x_sel, y_sel),
                radius,
                *[x[2] for x in sliders.values()],
                reset,
                width=432,
                height=ROW_HEIGHT,
                sizing_mode='fixed',
)
#                sizing_mode='scale_width')

need_reset = False
need_update = False

need_update_slider = False
maybe_update_slider = False
source = None
fig = None
precomputed = {}

def update_data(attr, old, new):
    global need_update

    need_update = True
    pass

def update_sliders(df, icol, sliders):
    """Update sliders based on the 'age' setting."""
    global need_slider_update, maybe_update_slider

    need_update_slider = True
    pass

def really_update_sliders(df, icol, sliders):
    debug(2, f'update sliders')

    if 'age' in precomputed:
        mi = sliders['age'][0]
        ma = sliders['age'][1]
        if mi.end+1 - mi.start >= 100:
            fuzz = (mi.end+1 - mi.start) // 100
        else:
            fuzz = (mi.end+1 - mi.start) // 10
            pass
        debug(2, f'{mi.value=} {mi.value+fuzz=}')
        xy = [(x,y) for (x,y) in precomputed['age'] if mi.value-fuzz <= x and mi.value >= x]
        debug(2, f'{xy=}')
        xy = [(x,y) for (x,y) in xy if ma.value <= y and ma.value+fuzz >= y]
        if len(xy) > 0:
            # for (x,y) in precomputed['age']:
            debug(2, f'{mi.value=} {ma.value=} {xy=}')
            (x,y) = xy[0]
            for d in precomputed['age'][(x,y)]:
                mi = precomputed['age'][(x,y)][d][0]
                ma = precomputed['age'][(x,y)][d][1]
                adjust_slider_pair(d, mi, ma)
                pass
            pass
        pass
    pass
    
# create the value selection range sliders
for c in icol:
    ma = df[c].max()
    mi = df[c].min()
    if ma != mi:
        smax = Slider(title=f'max {c}', value=ma, start=mi, end=ma, step=1, width=COL_WIDTH, height=ROW_HEIGHT)
        smin = Slider(title=f'min {c}', value=mi, start=mi, end=ma, step=1, width=COL_WIDTH, height=ROW_HEIGHT)

        class Kluge():
            def __init__(self, mi, ma, c):
                self._mi = mi
                self._ma = ma
                self._c = c
                self._disable = False
                pass

            def restrict(self, a, o, n):
                if self._disable is False:
                    self._disable = True

                    n = int(n)
                    debug(1, f'{self._c=}: {o=} {n=} {self._mi.value=} {self._ma.value=}')

                    smin = self._mi
                    smax = self._ma

                    if smin.value > n:
                        smin.value = n
                        pass
                    if smax.value < n:
                        smax.value = n
                        pass

                    if self._c == 'age':
                        update_sliders(df, icol, sliders)
                        pass
                    update_data(1,2,3)
                    self._disable = False
                    pass
                pass
            pass

        kluge = Kluge(smin, smax, c)
        sliders[c] = (smin, smax, row(smin, smax, width=300, height=ROW_HEIGHT, sizing_mode='fixed'))
        smin.on_change('value', kluge.restrict) # , kluge.update_data])
        smax.on_change('value', kluge.restrict) # , kluge.update_data])
        pass
    pass

def slider_touched(key):
    # debug(2, f'{min=}, {max=}, {min.start=}, {min.value=}, {max.value=}, {max.end=}')
    if key in ['age', 'ftp']:	# these are always checked, as they are reduced
        return True
    else:
        mi = sliders[key][0]
        ma = sliders[key][1]
        return (mi.value != mi.start or ma.value != ma.end)
    pass

def resize_slider_pair(key, low, high):
    a = sliders[key][0]
    b = sliders[key][1]
    debug(2, f'resize: {key=} {low=} {high=}')

    # a.start = b.start = a.value = low
    # a.end = b.end = b.value = high
    step = int((high - low) / 100)
    if step == 0:
        step = 1
        pass
    # a.step = b.step = step
    a.update(start=low, end=high, step=step, value=low)
    b.update(start=low, end=high, step=step, value=high)
    pass

def adjust_slider_pair(key, low, high):
    a = sliders[key][0]
    b = sliders[key][1]
    debug(2, f'adjust: {key=} {low=} {high=}')

    a.update(value=low)
    b.update(value=high)
    pass
    
# trim the max FTP
#resize_slider_pair('ftp', 0, 2000)
#resize_slider_pair('age', 0, 120)

def precompute_slider_updates(df, icol, sliders):
    """sic."""
    rv = {}
    for c in icol:
        smin, smax, _ = sliders[c]

        rv[c] = {}
        mi = smin.start
        ma = smin.end
        delta = ma+1-mi
        if delta > 100:
            delta = int(delta / 100)
        else:
            delta = int(delta / 10)
            pass

        for (x, y) in [ (x,y)
                        for x in range(int(mi), int(ma), delta)
                        for y in range(int(mi), int(ma), delta) if x < y ]:
            # debug(2, f'{mi=} {ma=} {delta=}: {x} < {c} and {c} <= {y}')
            eg = df.query(f'{x} < {c} and {c} <= {y}')
            rv[c][(x,y)] = {}
            for d in icol:
                if d is not c and len(eg[d]) > 0:
                    rv[c][(x,y)][d] = (eg[d].min(), eg[d].max())
                    pass
                pass
            pass
        pass
    return rv

# precomputed = precompute_slider_updates(df, icol, sliders)
# for (x,y) in precomputed['age']:
#    debug(2, f'{(x,y)=} {precomputed["age"][(x,y)]}')

def old_update_sliders(df, icol, sliders):
    """Update sliders based on the 'age' setting."""
    df = df.query(f'''{sliders['age'][0].value} <= age and age <= {sliders['age'][1].value}''')
    debug(2, f'{df=}')
    
    for c in icol:
        if c == 'age':
            continue

        ma = df[c].max()
        mi = df[c].min()
        adjust_slider_pair(c, mi, ma)
        pass
    pass
    
# Set up layouts and add to document
inputs = column(text,
                buto,
                row(x_sel, y_sel, width=2*COL_WIDTH, height=ROW_HEIGHT, sizing_mode='fixed'),
                radius,
                *[x[2] for x in sliders.values()],
                reset,
                width=COL_WIDTH+32+COL_WIDTH,
                sizing_mode='fixed')


for w in [radius, x_sel, y_sel]: # dropdown]:
    w.on_change('value', update_data)

def reset_callback(event):
    global need_reset

    need_reset = True
    pass


reset.on_event(ButtonClick, reset_callback)

def radio(a, b):
    """Make sure that at least one of the buttons is clicked."""
    if not a.active and not b.active:
        b.active = True
        pass
    update_data(1,2,3)
    
do_male.on_click(lambda event: radio(do_male, do_fema))
do_fema.on_click(lambda event: radio(do_fema, do_male))

def filter_chk(df, slid_key):
    """Generator for the filter check index."""
    for idx in df.index:	# for each row
        doit = True
        for c in df.columns:	# ..for each column
            if c in slid_key:	# .... if there is a slider
                (mi, ma, _) = sliders[c]
                v = df[c][idx]
                if mi.value <= v and v <= ma.value:
                    pass
                else:
                    doit = False
                    break
                pass
            pass
        if doit:
            yield idx
            pass
        pass
    pass

TOOLTIPS = """
    <div>
      <table>
        <tr>
         <td>
          <div>
            <img
                src="@imageSrc" height="128" alt="@imageSrc" width="128"
		style="float: left; margin: 0px 15px 15px 0px;"
                border="2"
            ></img>
          </div>
        </td>
        <td>
          <div>
            <span style="font-size: 17px; font-weight: bold;">@firstName</span>
            <span style="font-size: 17px; font-weight: bold;">@lastName</span>
          </div>

          <div>
            <span style="font-size: 10px; color: #696;">@age yo</span>
            <span style="font-size: 10px; color: #696;">@weight kg</span>
            <span style="font-size: 10px; color: #696;">@height cm</span>
            <span style="font-size: 10px; color: #696;">@ftp w</span>
          </div>
          <div>
            <span style="font-size: 10px; color: #696;">@country</span>
          </div>
        </td>
      </tr>
      </table>
    </div>
"""

def xy_plot_update(df, fig=None, source=None, male_glyph=None, fema_glyph=None):
    """Return the x-y plot data."""
    x = x_sel.value
    y = y_sel.value
    if x != y:
        data = {'male': df['male'],
                'x': df[x],
                'y': df[y],
                'age': df['age'],
                'ftp': df['ftp'],
                'imageSrc': df['imageSrc'],
                'weight': df['weight'],
                'height': df['height'],
                'firstName': df['firstName'],
                'lastName': df['lastName'],
                'country': df['countryAlpha3'],
        }
        if source is None:
            source = ColumnDataSource(data=data)
        else:
            source.data = data
            pass

        # only check sliders which have been touched
        slid_key = [c for c in sliders.keys() if slider_touched(c)]

        if len(slid_key) == 0:
            index = [i for i in df.index]
        else:
            index = [i for i in filter_chk(df, slid_key)]
            pass

        if do_male.active:
            is_male = [True if x == 1 else False for x in df['male']]
        else:
            is_male = [False for x in df['male']]
            pass
        if do_fema.active:
            is_fema = [True if x == 0 else False for x in df['male']]
        else:
            is_fema = [False for f in df['male']]
            pass

        vmale = CDSView(source=source, filters=[BooleanFilter(is_male), IndexFilter(index)])
        vfema = CDSView(source=source, filters=[BooleanFilter(is_fema), IndexFilter(index)])

        if fig is None:
            hov = HoverTool(tooltips=None)
            hov.tooltips = TOOLTIPS

            fig = figure(title=f'{x}::{y}',
                         x_axis_label=x,
                         y_axis_label=y,
                         tools=[hov, 'crosshair', 'box_zoom', 'reset'],
                         # active_drag='box_zoom',                        
                         sizing_mode='stretch_width', max_width=2560, plot_height=1024, plot_width=1280)

            male_glyph = fig.circle(source=source,
                                    view=vmale,
                                    x='x', y='y',
                                    legend_label='male',
                                    # radius=radius.value,
                                    size=radius.value,
                                    line_width=0,
                                    line_color='blue', fill_color='blue',
                                    hover_color='magenta',
                                    fill_alpha=CIRCLE_ALPHA)

            fema_glyph = fig.circle(source=source,
                                    view=vfema,
                                    x='x', y='y',
                                    legend_label='female',
                                    # radius=radius.value,
                                    size=radius.value,
                                    line_width=0,
                                    line_color='pink', fill_color='pink',
                                    hover_color='magenta',
                                    fill_alpha=CIRCLE_ALPHA)
        else:
            fig.title.text = f'{x}::{y}'
            fig.xaxis.axis_label = x
            fig.yaxis.axis_label = y
            male_glyph.glyph.size = radius.value
            fema_glyph.glyph.size = radius.value
            male_glyph.update(data_source=source, view=vmale)
            fema_glyph.update(data_source=source, view=vfema)
            
            pass

        text.value = f'{x}::{y} plot: {is_male.count(True)} male, {is_fema.count(True)} female'
        pass
    return fig, source, male_glyph, fema_glyph

fig, source, male_g, fema_g = xy_plot_update(df)
maybe_update = False

def update():
    global pro, df, fig, source, need_update, need_reset, male_g, fema_g
    global maybe_update
    global need_update_slider, maybe_update_slider
    
    if need_reset:
        pro = ZwiPro()
        fig, source, male_g, fema_g = xy_plot_update(df)
        curdoc().clear()
        curdoc().add_root(row(inputs, fig, sizing_mode='fixed', width=1280, height=1024))
        need_reset = False
        pass

    if need_update:
        maybe_update = True
        need_update = False
    elif maybe_update:
        maybe_update = False
        fig, source, male_g, fema_g = xy_plot_update(df, fig, source, male_g, fema_g)
        pass

    if need_update_slider:
        maybe_update_slider = True
        need_update_slider = False
    elif maybe_update_slider:
        maybe_update_slider = False
        really_update_sliders(df, icol, sliders)
        pass
    pass

curdoc().add_periodic_callback(update, 100)
curdoc().add_root(row(inputs, fig, sizing_mode='fixed', width=1280, height=1024))


