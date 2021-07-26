#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.

import sys
import os
import signal
import random
import time

import util
from util import ZwiPro, ZwiUser, DataBase, get_zdir
from dataclasses import dataclass

try:
    import click
except Exception as ex__:
    print('import error', ex__)
    raise SystemExit('please run: pip3 install click')

@click.option('-v', '--verbose', count=True)
@click.option('-d', '--debug', count=True)
@click.group()
def cli(verbose, debug):
    util.setup(verbose, debug)
    pass

@cli.command()
@click.option('--name', prompt='Enter Zwift username', help='Zwift username')
@click.password_option(help='Zwift password')
def auth(name, password):
    """Establish the authentication."""
    return util.auth(name, password)


@cli.command()
def check():
    """Verify that we have established the authentication."""
    return util.check()


@cli.command()
def clear():
    """Clear out any saved authentication information."""
    return util.clear()


@cli.command()
def wees():
    """Display followees who are not following me."""
    return followees()


@cli.command()
def wers():
    """Display followers who I am not following."""
    return followers()

def followees():
    count = 0
    usr = ZwiUser()
    for r in usr.wees:
        d = dict(zip(usr.cols, r))
        count += 1
        boo = (d['followeeStatusOfLoggedInPlayer'] != d['followerStatusOfLoggedInPlayer'])

        if util.verbo_p(1):
            # dump out entire list
            print('{:4d}{}{} {}\t{} {}'.format(count, [' ', '*'][boo]
                                               , d['followeeStatusOfLoggedInPlayer']
                                               , d['followerStatusOfLoggedInPlayer']
                                               , d['firstName'], d['lastName']))
        elif boo:
            # display only those whose soc status match
            print('{:4d} {} {}\t{} {}'.format(count
                                              , d['followeeStatusOfLoggedInPlayer']
                                              , d['followerStatusOfLoggedInPlayer']
                                              , d['firstName'], d['lastName']))
            pass
        pass
    print('processed {} followees'.format(count))
    pass


def followers():
    count = 0
    usr = ZwiUser()
    for r in usr.wers:
        d = dict(zip(usr.cols, r))
        count += 1
        boo = (d['followeeStatusOfLoggedInPlayer'] != d['followerStatusOfLoggedInPlayer'])

        if util.verbo_p(1):
            print('{:4d}{}{} {}\t{} {}'.format(count, [' ', '*'][boo]
                                               , d['followeeStatusOfLoggedInPlayer']
                                               , d['followerStatusOfLoggedInPlayer']
                                               , d['firstName'], d['lastName']))
        elif boo:
            # display only those whose soc status match
            print('{:4d} {} {}\t{} {}'.format(count
                                              , d['followeeStatusOfLoggedInPlayer']
                                              , d['followerStatusOfLoggedInPlayer']
                                              , d['firstName'], d['lastName']))
            pass
        pass
    print('processed {} followers'.format(count))
    pass


@click.option('--wers', is_flag=True)
@click.option('--wees', is_flag=True)
@cli.command()
def csv(wers, wees):
    """Generate CSV output, full table.  Writes to stdout."""
    import csv

    usr = ZwiUser()

    if wers:
        rows = usr.wers
    elif wees:
        rows = usr.wees
    else:
        raise SystemExit('No table selected.')
        pass

    with sys.stdout as out:
        writer = csv.DictWriter(out, fieldnames=usr.cols)
        writer.writeheader()
        for r in rows:
            d = dict(zip(usr.cols, r))
            writer.writerow(d)
            pass
        pass
    pass


@cli.command()
def reset():
    """Reset the database, refresh followers/followees data."""
    db = DataBase.db_connect(reset=True)
    ZwiUser(db, update=True)
    ZwiPro().update(force=True)

    return 0


@cli.command()
def update():
    """Update user's follower/follee DB cache."""
    ZwiUser(update=True)
    ZwiPro().update(force=True)

    return 0

@dataclass
class ProPrinter():
    line_cnt: int = 0  # output line count

    def out(self, p, prefix=' '):
        self.line_cnt += 1
        if self.line_cnt % 32 == 1:
            print((' ' +
                  '{0:18.18s} {1:>8.8s} {2:>4.4s} ' +
                  '{3:>5.5s} ' +
                  '{4:>6.6s} ' +
                  '{5:>8.8s} ' +
                  '{6:>8.8s} ' +
                  '{7:16.16s} ' +
                  '{8:s}').format(
                      'date',
                      'ZwiftID',
                      'FTP',
                      'level',
                      'hours',
                      'distance',
                      'climbed',
                      'bike',
                      'name'))
            pass
        print(prefix +
              f'{p.addDate:18.18s} {p.id:8d} {p.ftp:4d} ' +
              f'{p.achievementLevel/100.0:5.2f} ' +
              f'{p.totalTimeInMinutes//60:6d} ' +
              f'{p.totalDistance:8d} ' +
              f'{p.totalDistanceClimbed:8d} ' +
              f'{p.virtualBikeModel:16.16s} ' +
              f'{p.firstName} {p.lastName}')
        pass
    pass

@cli.command()
@click.option('--force', is_flag=True, help='Force refresh.')
def pro_update(force):
    """Update the profile DB based on user's follower/followee DB cache."""
    usr = ZwiUser()
    pro = ZwiPro()
    pr = ProPrinter()

    for r in usr.wers:
        d = dict(zip(usr.cols, r))
        new = pro.update(zid=d['followerId'], force=force)
        if util.verbo_p(1) and new:
            pr.out(new)
        pass

    for r in usr.wees:
        d = dict(zip(usr.cols, r))
        new = pro.update(zid=d['followeeId'], force=force)
        if util.verbo_p(1) and new:
            pr.out(new)
        pass

    return 0

        
@cli.command()
def pro_list():
    """List profile DB contents."""

    pro = ZwiPro()
    pr = ProPrinter()

    for p in ZwiPro():
        pr.out(p)
        pass
    return 0

@cli.command()
@click.option('--skip', help='skip over the first N profile entries')
@click.option('--zid', help='update just the profile entry for the given Zwift ID')
@click.option('--seek', help='seek into the list of entries up to the specified Zwift ID')
def pro_refresh(skip, zid, seek):
    """Refresh local profile DB from Zwift."""
    skip = 0 if skip is None else int(skip)

    pro = ZwiPro()
    pr = ProPrinter()

    for p in pro:
        if skip > 0:
            skip -= 1
            continue

        if zid is not None and int(zid) != int(p.id):
            continue
        if seek is not None and int(seek) != int(p.id):
            continue

        q = p.update(pro)
        pr.out(p)
        if q is None:
            # Sometimes the update fails.
            print(f'skipping {p.id}')
        elif p is not q and p != q:
            pr.out(q, prefix='*')
            util.verbo(1, f'{p.last_difference}')
            pass

        if zid: break
        if seek: seek = None
        pass
    return 0


@cli.command()
def gui():
    """ZwiView."""
    try:
        import PyQt5
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QPalette, QColor
        from PyQt5 import QtCore, QtGui, QtWidgets, uic
        from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTableWidget
        from PyQt5.QtCore import (pyqtSignal, QPointF, QRect, QSize, Qt, QTimer,
                                  QFile,
                                  QRunnable, QThreadPool, QMutex, QSemaphore)
        from PyQt5.QtGui import (QPainter, QPolygonF, QIcon, QPixmap, QBrush, QPen, QColor, QFont)
        from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QStyle,
                                     QStyledItemDelegate, QTableWidget, QTableWidgetItem, QWidget,
                                     QGridLayout,
                                     QDialog, QLineEdit, QMessageBox,
                                     QMainWindow,
                                     QGraphicsScene,
                                     QStyleOptionViewItem)
    except Exception as e:
        print('import error:', e)
        print('pip3 install pyqt5')
        sys.exit(1)
        pass

    try:
        sdir = os.path.dirname(os.path.realpath(__file__)) + os.sep
        sfile  = sdir + 'zwi_ui_v0.ui'
        Ui_MainWindow, QtBaseClass = uic.loadUiType(sfile)
    except Exception as e:
        print(f'{e}')
        raise SystemExit(f"Can't find GUI script file: {sfile}.")

    class ImageCache(QRunnable):
        def __init__(self, sig):
            super().__init__()
            self.setAutoDelete(False)
            self._queue = list()
            self._done = list()
            self._cache = dict()
            self._context = self._ssl_kluge()
            self._threads = list()
            self._path = get_zdir('.image-cache')
            self._mux = QMutex()
            self._requ = QSemaphore()
            self._resp = QSemaphore()
            self._pool = QThreadPool.globalInstance()
            self._sig = sig
            self._terminate = False
            self._nthreads = 0
            pass

        def load(self, key, widget):
            """Load an image into the cache."""
            # print(f'{self=} {key=}')
            self._mux.lock()
            if key in self._cache:
                px = self._cache[key]
            else:
                self._cache[key] = px = None
                self._queue.insert(0, (key, widget))
                self._requ.release()
                if self._nthreads == 0:
                    self._terminate = False
                    self._pool.start(self)
                    self._nthreads = 1
                    pass
                pass
            self._mux.unlock()
            return px

        def autoDelete(self):
            print(f'autodel: {self=}')
            return False
        
        def stop(self):
            while True:
                self._mux.lock()
                if self._nthreads > 0:
                    # XXX: what about if it is blocked on a semaphore?
                    self._terminate = True
                    print('waiting for thread to terminate....')
                    time.sleep(1)
                else:
                    self._mux.unlock()
                    return
                pass
            pass

        def run(self):
            """Thread function."""
            # print(f'running: {self=}')
            while True:
                self._requ.acquire()
                self._mux.lock()
                if self._terminate:
                    if len(self._queue) != 0:
                        # print(f'{self=} {self._terminate=} {self._nthreads=} {self._queue=}')
                        self._terminate = False
                    else:
                        self._terminate = False
                        self._nthreads = 0
                        assert len(self._queue) == 0
                        self._mux.unlock()
                        return
                    pass

                if len(self._queue) == 0:
                    # print(f'wtf? {len(self._queue)=}')
                    wrk = None
                else:
                    wrk = self._queue.pop()
                    pass
                self._mux.unlock()
                if wrk is None:
                    continue

                key = wrk[0]
                if key == 'None' or 'http' not in key:
                    continue  # some are None???

                path = f'''{self._path}/{key.split('/')[-1]}'''
                if not os.path.isfile(path):
                    self._fetch(key, path)
                    pass

                if os.path.isfile(path):
                    self._mux.lock()
                    self._done.insert(0, wrk)
                    self._mux.unlock()
                    self._sig.emit(1)
                    pass
                time.sleep(.001)
                pass
            pass

        @staticmethod
        def _ssl_kluge():
            """Need this to avoid certificate validation errors."""
            import ssl
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context

        def update(self):
            self._mux.lock()
            while len(self._done) > 0:
                wrk = self._done.pop()
                key, wid = wrk[0], wrk[1]
                px = self._cache[key] = QPixmap(f'''{self._path}/{key.split('/')[-1]}''')
                self._mux.unlock()
                wid.imageLoaded(key, px)
                self._mux.lock()
                pass

            # see if we are all done
            if len(self._queue) == 0 and not self._terminate and self._nthreads > 0:
                # print(f'request thread to terminate')
                self._terminate = True
                self._requ.release()
                pass
            self._mux.unlock()
            pass

        def _fetch(self, url, path):
            """Try to fetch the resource and stack in file."""
            import shutil
            import urllib.request

            try:
                with urllib.request.urlopen(url, context=self._context) as resp:
                    f = open(path, 'wb')
                    shutil.copyfileobj(resp, f)
                    f.close()
            except Exception as e:
                print(f'oops: {e}')
                self._mux.lock()
                del self._cache[url]
                try:
                    os.remove(path)
                except Exception as e:
                    pass
                self._mux.unlock()
                pass
            pass

        pass

    pass

    class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
        sig = pyqtSignal(int, name='results')

        def __init__(self):
            QtWidgets.QMainWindow.__init__(self)
            Ui_MainWindow.__init__(self)
            self.setupUi(self)
            self.setup()
            pass
    
        def setup(self):
            self._timer = None
            self._status = self.statusBar()
            self._status.showMessage('Hi there')
            self.sig.connect(self.handle)

            # ZwiView menu
            self.actionwees.triggered.connect(self.doWees)
            self.actionwers.triggered.connect(self.doWers)
            self.actionauto.triggered.connect(self.doAuto)
            self.actionnext.triggered.connect(self.doNext)
            self.actionprev.triggered.connect(self.doPrev)
            self.actionquit.triggered.connect(self.doQuit)
            # reset menu
            self.actionicache.triggered.connect(self.doResetIcache)
            self.actiondbase.triggered.connect(self.doResetDBase)
            self.actionauthen.triggered.connect(self.doResetAuthen)
            # sort menu
            self.actionfirst_name.triggered.connect(self.doSortFirstName)
            self.actionlast_name.triggered.connect(self.doSortLastName)
            self.actionplayer_type.triggered.connect(self.doSortPlayerType)
            self.actioncountry.triggered.connect(self.doSortCountry)
            # search menu
            self.actionsearch.triggered.connect(self.doSearch)
            # scroll bar
            self.sb.valueChanged.connect(self.sbValueChanged)

            self._usr = ZwiUser()
            self._icache = ImageCache(self.sig)
            self.switch('wers')
            pass

        def sbValueChanged(self, val):
            self._idx = val
            # self.refresh must keep _idx in range
            self.refresh(0, fromsb=True)
            pass
                
        def doWees(self):
            self.switch('wees')
            pass

        def doWers(self):
            self.switch('wers')
            pass

        def doAuto(self):
            if self._timer is None:
                self._timer = QTimer()
                self._timer.timeout.connect(lambda: self.refresh(1))
                self._timer.start(2*1000)
            else:
                self._timer.stop()
                del self._timer
                self._timer = None
                pass
            pass

        def doNext(self):
            if self._timer:
                i = self._timer.interval()
                if i < 30*1000:
                    # going slower: just set the interval
                    self._timer.setInterval(i*2)
                    pass
                return
            self.refresh(1)
            pass

        def doPrev(self):
            if self._timer:
                i = self._timer.interval()
                if i > 10:
                    # going faster: stop and restart
                    self._timer.stop()
                    self._timer.start(i/2)
                    pass
                return
            self.refresh(-1)
            pass

        def doQuit(self):
            self.close()
            pass

        def doResetIcache(self):
            """Reset the image cache."""
            self._icache = ImageCache(self.sig)
            pass
            
        def doResetDBase(self):
            """Reset the local data base cache of Zwift data."""
            db = DataBase.db_connect(reset=True)
            ZwiUser(db, update=True)
            self.switch('wers')	# necessary(?) side effect.
            pass

        def doResetAuthen(self):
            """(eventually)Reset the Zwift user authentication."""
            return self.message('Use `zwi clear` to reset the Zwift user authentication.')
            
        def doSortFirstName(self):
            self.doSort('firstName')
            pass
        
        def doSortLastName(self):
            self.doSort('lastName')
            pass
        
        def doSortPlayerType(self):
            self.doSort('playerType')
            pass

        def doSortCountry(self):
            self.doSort('countryAlpha3')
            pass
        
        def doSort(self, col):
            """Sort current table by country."""
            idx = self._usr.cols.index(col)
            rev = self.actionreverse.isChecked()

            def sel(elem):
                return elem[idx]

            self._data = sorted(self._data, key=sel, reverse=rev)
            self._idx = 0
            self.refresh(0)
            pass
            
        def doSearch(self):
            """(eventually) search."""
            return self.message('Yet to be implemented.')

        def message(self, msg='Oops!'):
            """Raise a modal dialog."""
            f = QMessageBox(parent=self)
            f.setText(msg)
            return f.exec_()
            
        def close(self):
            if self._timer:
                self._timer.stop()
                pass
            if self._icache:
                self._icache.stop()
                pass
            super().close()
            pass

        def handle(self, index):
            self._icache.update()
            pass

        def switch(self, which):
            if which == 'wers':
                self._data = self._usr.wers
            else:
                self._data = self._usr.wees
                pass
            self._idx = 0
            self._max = len(self._data)-1
            self.sb.setMaximum(self._max)
            self.sb.setMinimum(0)
            self.setWindowTitle(f'ZwiView -- follo{which}')
            self.refresh(0)
            pass
        
        def refresh(self, delta=0, fromsb=False):
            self._idx += delta
            if self._idx > self._max:
                self._idx = 0
            elif self._idx < 0:
                self._idx = self._max
                pass
                
            if fromsb == False:
                self.sb.setValue(self._idx)
                pass
            
            try:
                r = self._data[self._idx]
            except Exception as e:
                print(f'{e=} {self._idx=} {self._max=} {len(self._data)=}')
                return
            
            d = dict(zip(self._usr.cols, r))
            self.firstName.setText(d['firstName'])
            self.lastName.setText(d['lastName'])

            if d['followerStatusOfLoggedInPlayer'] == 'IS_FOLLOWING':
                self.isWer.setText('following')
            else:
                self.isWer.setText('not following: ' + d['followerStatusOfLoggedInPlayer'])
                pass

            if d['followeeStatusOfLoggedInPlayer'] == 'IS_FOLLOWING':
                self.isWee.setText('followed')
            else:
                self.isWee.setText('not followed: ' + d['followeeStatusOfLoggedInPlayer'])
                pass

            self.country.setText(f'''     country: {d['countryAlpha3']}''')
            self.rtype.setText(  f'''player type: {d['playerType']}''')
            
            boo = (d['followeeStatusOfLoggedInPlayer'] != d['followerStatusOfLoggedInPlayer'])
            url = d['imageSrc']
            if d == 'None':
                url = d['imageSrcLarge']
                pass

            scene = QGraphicsScene()
            if url == 'None':
                scene.addText('No image provided')
                self._status.showMessage(f'{1+self._idx}')
            else:
                px = self._icache.load(url, self)
                if px is not None:
                    scene.addPixmap(px)
                    self._status.showMessage(f'{1+self._idx}')
                else:
                    scene.addText('loading...')
                    self._status.showMessage(url + ' -- loading')
                    self._image_load_key = url
                    pass
                pass

            self.graphicsView.setScene(scene)
            self.graphicsView.show()
            self.show()
            pass

        def imageLoaded(self, key, px):
            if key == self._image_load_key:
                scene = QGraphicsScene()
                scene.addPixmap(px)
                self.graphicsView.setScene(scene)
                self.graphicsView.show()
                self.show()
                self._status.showMessage(f'{1+self._idx}')
                pass
            pass
            
        pass
    

    app = QtWidgets.QApplication([])
    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")

    # Now use a palette to switch to dark colors:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.yellow)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.yellow)
    palette.setColor(QPalette.Text, Qt.green)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.green)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
    pass


# disable this ...
# @cli.command()
def devel():
    """more development staging...."""

    usr = ZwiUser()
    pro = ZwiPro()

    # pro.update(pr.player_id)

    count = 0
    for r in usr.wees:
        d = dict(zip(usr.cols, r))
        pro.update(d['followeeId'])
        if util.verbo_p(0):
            print(f'''\rprocessed {d['followeeId']}: {count}''', end='')
            pass
        count += 1
        pass
    util.verbo(0, '')

    count = 0
    for r in usr.wers:
        d = dict(zip(usr.cols, r))
        pro.update(d['followerId'])
        if util.verbo_p(0):
            print(f'''\rprocessed {d['followerId']}: {count}''', end='')
            pass
        count += 1
        pass
    util.verbo(0, '')

    # see if I can get follower[0]'s followee list
    # print(f'uid={usr.wers[0][0]}')
    # usr0 = ZwiUser(uid=usr.wers[0][0], update=True, pro_update=True)
    util.setup(1, util.util.debug_lvl)
    
    count = 0
    for r in pro._pro:
        d = dict(zip(pro.cols, r))
        if d['id'] == 1277086:
            continue

        print(f'{d["id"]}')
        ZwiUser(uid=d['id'], update=True, pro_update=pro)
        if util.verbo_p(1):
            print(f'''processed {d['id']}: {count}''')
            pass
        count += 1
        pass
    pass

    
# disable this ...
# @cli.command()
def flask_test():
    """Test using flask to serve the image cache."""
    return 0
    
    
# disable this ...
# @cli.command()
def test():
    """Test some things...."""
    import flask
    from flask import Flask, redirect, send_file
    from markupsafe import escape
    
    def process(self, wrk):
        """Process completed URL fetch."""
        print(f'process: {wrk=}')
        url = wrk[0]
        pass
    
    def callback(cache):
        """This callback is called in the worker thread."""
        print(f'callback: {cache=}')
        cache.update(process)
        pass

    idir = get_zdir('.image-cache')
    cache = util.AssetCache(idir, callback)
    app = Flask(__name__)

    @app.route('/<req>')
    def root(req):
        print(f'root: {req=}')
        return escape(req)

    @app.route('/images/<img>')
    def images(img):
        print(f'images: {escape(img)}')
            
        try:
            fna = cache.load('https://static-cdn.zwift.com/prod/profile/' + img, {})
            if fna:
                print(f'cache.load: => {fna}')
                return flask.send_file(fna,
                                       as_attachment=False,
                                       download_name=f'{img}.jpg',
                                       mimetype='image/jpeg')
            else:
                return flask.redirect('https://static-cdn.zwift.com/prod/profile/' + img, code=307)
        except Exception as ex:
            print(f'/images/{escape(img)}: {ex=}')
            return flask.Response(f'/images/{escape(img)}: {ex=}')
        pass

    app.run()

    return 0

def keyboardInterruptHandler(signal, frame):
    print("KeyboardInterrupt (signal: {}) has been caught. Cleaning up...".format(signal))
    sys.exit(0)


# XXX: This works, but not entirely.
# I find I have to interact with the GUI to get it to fire
# after ^C
#
signal.signal(signal.SIGINT, keyboardInterruptHandler)

if __name__ == '__main__':
    try:
        cli()
        sys.exit(0)
    except Exception as e:
        util.debug(2, f'{type(e)=}\n{e!r}')
        print(f'{e}')
        if util.debug_p(0):
            raise Exception('oops!') from e
        sys.exit(1)
    pass
