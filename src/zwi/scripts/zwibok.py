# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.
"""Bokeh-based interface to ZwiPro profile data."""

import os
import sys
import time
import signal
import functools
from threading import Thread
import zwi
from zwi import ZwiPro, debug, debug_p, verbo, get_zdir

try:
    import click
    import bokeh
    import pandas as pd
    import numpy as np
except Exception as e:
    print('import error', e)
    raise SystemExit('use `pip3 install` to install missing modules.')

from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.embed import server_document
from bokeh.events import ButtonClick
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput, Dropdown, Select
from bokeh.models import CDSView, GroupFilter, BooleanFilter, IndexFilter
from bokeh.models import Button, Toggle, HoverTool
from bokeh.models.glyphs import Text, Rect
from bokeh.models.annotations import Title
from bokeh.plotting import figure, show, output_notebook
from bokeh.server.server import Server
from bokeh.server.server import Server
from bokeh.themes import Theme
from tornado.ioloop import IOLoop

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

#
# adjust some values
#
def minmax(x, mi, ma):
    if x < mi:
        return mi
    if x > ma:
        return ma
    return x

NONE = 'https://upload.wikimedia.org/wikipedia/commons/c/ce/Image_of_none.svg'

def map_none(x):
    if x is None or x == 'None':
        return NONE
    else:
        return x
    pass

COL_WIDTH    = 200
ROW_HEIGHT   = 48
CIRCLE_ALPHA = 0.7

class ZwiBok(object):
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

    def __init__(self, doc):
        self.doc = doc
        # Set up widgets
        self.text = TextInput(title='', value='',
                              width=2*COL_WIDTH, height=ROW_HEIGHT)
        self.x_sel = Select(value='age', title='X', options=self.icol,
                            width=COL_WIDTH, height=ROW_HEIGHT)
        self.y_sel = Select(value='ftp', title='Y', options=self.icol,
                            width=COL_WIDTH, height=ROW_HEIGHT)
        self.reset = Button(label='reset', width=COL_WIDTH, height=ROW_HEIGHT)
        self.radius = Slider(title='radius', value=10, start=1, end=20, step=1,
                             width=COL_WIDTH, height=ROW_HEIGHT)
        self.do_male = Toggle(label='male', active=True,
                              width=COL_WIDTH, height=ROW_HEIGHT)
        self.do_fema = Toggle(label='female', active=True,
                              width=COL_WIDTH, height=ROW_HEIGHT)
        self.buto = row(self.do_male, self.do_fema,
                        width=2*COL_WIDTH, height=ROW_HEIGHT)

        self.need_reset = False
        self.need_update = False
        self.maybe_update = False
        self.need_update_slider = False
        self.maybe_update_slider = False
        self.precomputed = {}

        self.refresh_profile()
        self.setup_sliders()

        for w in [self.radius, self.x_sel, self.y_sel]: # dropdown]:
            w.on_change('value', self.update_data)
            pass

        self.reset.on_event(ButtonClick, self.reset_callback)

        self.do_male.on_click(lambda event: self.radio(self.do_male, self.do_fema))
        self.do_fema.on_click(lambda event: self.radio(self.do_fema, self.do_male))

        self.source = None
        self.fig = None
        self.xy_plot_update(reset=True)

        # Set up layouts and add to document
        self.inputs = column(self.text,
                             self.buto,
                             row(self.x_sel, self.y_sel,
                                 width=2*COL_WIDTH, height=ROW_HEIGHT,
                                 sizing_mode='fixed'),
                             self.radius,
                             *[x[2] for x in self.sliders.values()],
                             self.reset,
                             width=COL_WIDTH+32+COL_WIDTH,
                             sizing_mode='fixed')

        self.doc.add_periodic_callback(self.update, 100)
        self.doc.add_root(row(self.inputs, self.fig, sizing_mode='fixed',
                              width=1280, height=1024))
        pass

    def refresh_profile(self):
        self.pro = ZwiPro()
        df = pro_to_df(self.pro, self.col)
        df['age'] = df['age'].apply(lambda x: minmax(x, 0, 120))
        df['ftp'] = df['ftp'].apply(lambda x: minmax(x, 0, 2000))
        df['achievementLevel'] = df['achievementLevel'].apply(lambda x: int(x) // 100)
        df['weight'] = df['weight'].apply(lambda x: int(x) // 1000)
        df['height'] = df['height'].apply(lambda x: int(x) // 10)
        df['totalDistance'] = df['totalDistance'].apply(lambda x: int(x) // 1000)
        df['imageSrc'] = df['imageSrc'].apply(lambda x: map_none(x))

        self.df = df
        pass

    def setup_sliders(self):
        """Setup the sliders based on the limits of the current DataFrame."""
        
        # slider restriction function: used below
        def do_restrict(smin, smax, c, cb, a,b,n):
            """Callback function to modify data based on slider settings."""
            debug(3, f'restrict: {c=} {smin.value=} {smax.value=} {cb=} {n=}')
            self.doc.hold(policy='combine')	# combine all events

            n = int(n)
            if smin.value > n:
                smin.value = n
                pass
            if smax.value < n:
                smax.value = n
                pass

            if c == 'age':
                self.update_sliders(self.df, self.icol, self.sliders)
                pass
            self.update_data(1,2,3)
            self.doc.unhold()
            pass

        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        # This was rather difficult to get to work.
        # If I put the lambda function in the on_change() call,
        # even though I get distinct lambda's generated,
        # the `cb` is the last one returned from gen_restrict()
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        def gen_restrict(smin, smax, c):
            cb = functools.partial(do_restrict, smin, smax, c)            
            return lambda a, b, n: cb(cb, a,b,n) 

        # create the value selection range sliders
        wtf={}
        self.sliders = {}
        for c in self.icol:
            ma = self.df[c].max()
            mi = self.df[c].min()
            if ma != mi:
                smax = Slider(title=f'max {c}', value=ma, start=mi, end=ma,
                              step=1, width=COL_WIDTH, height=ROW_HEIGHT)
                smin = Slider(title=f'min {c}', value=mi, start=mi, end=ma,
                              step=1, width=COL_WIDTH, height=ROW_HEIGHT)

                self.sliders[c] = (smin, smax, row(smin, smax, width=300,
                                                   height=ROW_HEIGHT, sizing_mode='fixed'))

                cb = gen_restrict(smin, smax, c)
                if debug_p(3):
                    print(f'sliders: {c=} {smin=} {smax=} {cb=}')
                    # only cache this if debugging.
                    wtf[c] = cb
                    pass
                smin.on_change('value_throttled', cb)
                smax.on_change('value_throttled', cb)
                pass
            pass
        
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        # This was just to debug the problems with setting the on_change() when
        # lambda was always using the last `cb = gen_restrict()` value.
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        # How do I write a test to ensure I have this right going forward?
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        for c in wtf.keys():
            print(f'wtf? {c=} {wtf[c]=}')
            smin, smax, _ = self.sliders[c]
            print(f'{smin=} {smin._callbacks.get("value_throttled")=}')
            print(f'{smax=} {smax._callbacks.get("value_throttled")=}')
            smin.trigger('value_throttled', 1, 2)
            smax.trigger('value_throttled', 2, 3)
            pass
        pass

    def refresh_sliders(self):
        """Adjust the sliders when the DataFrame changes."""
        for c in self.sliders.keys():
            ma = self.df[c].max()
            mi = self.df[c].min()
            self.resize_slider_pair(c, mi, ma)
            pass
        pass

    def update_data(self, attr, old, new):
        self.need_update = True
        pass

    def update_sliders(self, df, icol, sliders):
        """Update sliders based on the 'age' setting."""
        self.need_update_slider = True
        pass

    def really_update_sliders(self, df, icol, sliders):
        debug(2, f'update sliders')

        if 'age' in self.precomputed:
            mi = self.sliders['age'][0]
            ma = self.sliders['age'][1]
            if mi.end+1 - mi.start >= 100:
                fuzz = (mi.end+1 - mi.start) // 100
            else:
                fuzz = (mi.end+1 - mi.start) // 10
                pass
            debug(2, f'{mi.value=} {mi.value+fuzz=}')
            xy = [(x,y) for (x,y) in self.precomputed['age']
                  if mi.value-fuzz <= x and mi.value >= x]
            debug(2, f'{xy=}')
            xy = [(x,y) for (x,y) in xy if ma.value <= y and ma.value+fuzz >= y]
            if len(xy) > 0:
                # for (x,y) in self.precomputed['age']:
                debug(2, f'{mi.value=} {ma.value=} {xy=}')
                (x,y) = xy[0]
                for d in self.precomputed['age'][(x,y)]:
                    mi = self.precomputed['age'][(x,y)][d][0]
                    ma = self.precomputed['age'][(x,y)][d][1]
                    self.adjust_slider_pair(d, mi, ma)
                    pass
                pass
            pass
        pass
    
    def slider_touched(self, key):
        if key in ['XX_NO_MORE_age', 'XX_NO_MORE_ftp']:
	    # these are XX_NO_MORE_always checked, as they are reduced
            return True
        else:
            mi = self.sliders[key][0]
            ma = self.sliders[key][1]
            return (mi.value != mi.start or ma.value != ma.end)
        pass

    def resize_slider_pair(self, key, low, high):
        a = self.sliders[key][0]
        b = self.sliders[key][1]
        debug(2, f'resize: {key=} {low=} {high=}')

        step = int((high - low) / 100)
        if step == 0:
            step = 1
            pass
        a.update(start=low, end=high, step=step, value=low)
        b.update(start=low, end=high, step=step, value=high)
        pass

    def adjust_slider_pair(self, key, low, high):
        a = self.sliders[key][0]
        b = self.sliders[key][1]
        debug(2, f'adjust: {key=} {low=} {high=}')

        a.update(value=low)
        b.update(value=high)
        pass
    
    def precompute_slider_updates(self):
        """sic."""
        rv = {}
        for c in self.icol:
            smin, smax, _ = self.sliders[c]

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
                eg = self.df.query(f'{x} < {c} and {c} <= {y}')
                rv[c][(x,y)] = {}
                for d in self.icol:
                    if d is not c and len(eg[d]) > 0:
                        rv[c][(x,y)][d] = (eg[d].min(), eg[d].max())
                        pass
                    pass
                pass
            pass
        return rv

    # self.precomputed = precompute_slider_updates(df, icol, sliders)
    # for (x,y) in self.precomputed['age']:
    #    debug(2, f'{(x,y)=} {self.precomputed["age"][(x,y)]}')

    def old_update_sliders(self, df, icol, sliders):
        """Update sliders based on the 'age' setting."""
        self.df = self.df.query(f'{self.sliders["age"][0].value} <= age and age <= {self.sliders["age"][1].value}')
        debug(2, f'{df=}')
    
        for c in self.icol:
            if c == 'age':
                continue

            ma = self.df[c].max()
            mi = self.df[c].min()
            self.adjust_slider_pair(c, mi, ma)
            pass
        pass
    
    def reset_callback(self, event):
        self.need_reset = True
        pass


    def radio(self, a, b):
        """Make sure that at least one of the buttons is clicked."""
        if not a.active and not b.active:
            b.active = True
            pass
        self.update_data(1,2,3)
        pass

    def filter_chk(self, df, slid_key):
        """Generator for the filter check index."""
        for idx in self.df.index:	# for each row
            doit = True
            for c in self.df.columns:	# ..for each column
                if c in slid_key:	# .... if there is a slider
                    (mi, ma, _) = self.sliders[c]
                    v = self.df[c][idx]
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
            <span style="font-size: 10px; color: #696;">yo:@age</span>
            <span style="font-size: 10px; color: #696;">kg:@weight</span>
            <span style="font-size: 10px; color: #696;">cm:@height</span>
            <span style="font-size: 10px; color: #696;">ftp:@ftp</span>
          </div>

          <div>
            <span style="font-size: 10px; color: #696;">lvl:@level</span>
            <span style="font-size: 10px; color: #696;">km:@distance</span>
            <span style="font-size: 10px; color: #696;">m:@climbed</span>
          </div>
          <div>
            <span style="font-size: 10px; color: #696;">country:@country</span>
          </div>
        </td>
      </tr>
      </table>
    </div>
    """

    def xy_plot_update(self, reset=False):
        """Update the x-y plot data."""
        df = self.df
        x = self.x_sel.value
        y = self.y_sel.value
        if x != y:  # select X::Y axes so long as they differ
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
                    'distance': df['totalDistance'],
                    'climbed': df['totalDistanceClimbed'],
                    'level': df['achievementLevel'],
            }
            if reset:
                self.source = ColumnDataSource(data=data)
            else:
                assert self.source is not None
                self.source.data = data
                pass

            # only check sliders which have been touched
            slid_key = [c for c in self.sliders.keys() if self.slider_touched(c)]

            if len(slid_key) == 0:
                index = [i for i in df.index]
            else:
                index = [i for i in self.filter_chk(df, slid_key)]
                pass

            if self.do_male.active:
                is_male = [True if x == 1 else False for x in df['male']]
            else:
                is_male = [False for x in df['male']]
                pass
            if self.do_fema.active:
                is_fema = [True if x == 0 else False for x in df['male']]
            else:
                is_fema = [False for f in df['male']]
                pass

            vmale = CDSView(source=self.source, filters=[BooleanFilter(is_male),
                                                         IndexFilter(index)])
            vfema = CDSView(source=self.source, filters=[BooleanFilter(is_fema),
                                                         IndexFilter(index)])

            if reset:
                hov = HoverTool(tooltips=None)
                hov.tooltips = self.TOOLTIPS

                self.fig = fig = figure(title=f'{x}::{y}',
                                        x_axis_label=x,
                                        y_axis_label=y,
                                        tools=[hov, 'crosshair', 'box_zoom', 'reset'],
                                        sizing_mode='stretch_width',
                                        max_width=2560,
                                        plot_height=1024, plot_width=1280)

                self.male_g = fig.circle(source=self.source,
                                         view=vmale,
                                         x='x', y='y',
                                         legend_label='male',
                                         size=self.radius.value,
                                         line_width=0,
                                         line_color='blue', fill_color='blue',
                                         hover_color='magenta',
                                         fill_alpha=CIRCLE_ALPHA)

                self.fema_g = fig.circle(source=self.source,
                                         view=vfema,
                                         x='x', y='y',
                                         legend_label='female',
                                         size=self.radius.value,
                                         line_width=0,
                                         line_color='pink', fill_color='pink',
                                         hover_color='magenta',
                                         fill_alpha=CIRCLE_ALPHA)
            else:
                self.fig.title.text = f'{x}::{y}'
                self.fig.xaxis.axis_label = x
                self.fig.yaxis.axis_label = y
                self.male_g.glyph.size = self.radius.value
                self.fema_g.glyph.size = self.radius.value
                self.male_g.update(data_source=self.source, view=vmale)
                self.fema_g.update(data_source=self.source, view=vfema)
                pass

            s = f'{x}::{y} plot: {is_male.count(True)} male,'
            s += f'{is_fema.count(True)} female'
            self.text.value = s
            pass
        pass

    def update(self):
        if self.need_reset:
            # reset by refreshing the ZwiPro
            self.pro = ZwiPro()
            self.refresh_profile()
            self.refresh_sliders()
            self.xy_plot_update()
            self.doc.clear()
            self.doc.add_root(row(self.inputs, self.fig, sizing_mode='fixed',
                                  width=1280, height=1024))
            self.need_reset = False
            pass

        if self.need_update:
            self.maybe_update = True
            self.need_update = False
        elif self.maybe_update:
            self.maybe_update = False
            self.xy_plot_update()
            pass

        if self.need_update_slider:
            self.maybe_update_slider = True
            self.need_update_slider = False
        elif self.maybe_update_slider:
            self.maybe_update_slider = False
            self.really_update_sliders(self.df, self.icol, self.sliders)
            pass
        pass

    pass

def zwibok(doc):
    zwibok = ZwiBok(doc)
    pass

def keyboardInterruptHandler(signal, frame):
    print("KeyboardInterrupt (signal: {}) has been caught. Cleaning up...".format(signal))
    sys.exit(0)


@click.option('-v', '--verbose', count=True)
@click.option('-d', '--debug', count=True)
@click.group()
def cli(verbose, debug):
    zwi.setup(verbose, debug)
    pass

@click.option('--port', default=5006, help='Run on specified port.')
@cli.command()
def serve(port):
    """Run ZwiBok server."""

    server = Server({
        '/zwibok': zwibok,
    }, num_procs=1, port=port)
    server.start()

    print(f'Opening ZwiBok application on http://localhost:{port}/')
    signal.signal(signal.SIGINT, keyboardInterruptHandler)
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
    pass

def main():
    try:
        cli()
    except Exception as e:
        debug(2, f'{type(e)=}\n{e!r}')
        print(f'{e}')
        if debug_p(0):
            raise Exception('oops!') from e
        sys.exit(1)
    pass

    
"""
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

    if False:
        # XXXXXXXx not working yet
        df['imageSrc'] = df['imageSrc'].apply(lambda x: ic_lookup(x, df))
        print(df['imageSrc'])
        pass

"""
