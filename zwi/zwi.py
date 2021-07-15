#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# I follow all those who do not follow themselves.  Who follows me?
#
#
# Usage: ./zwi.py --help
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.
#

import sys
import os
import time
import sqlite3 as sq
from datetime import datetime
from dataclasses import dataclass, asdict, astuple, fields

try:
    from zwift import Client
    import keyring
    import click
except Exception as e:
    print('import error', e)
    print('pip3 install zwift-client keyring click')
    sys.exit(1)
    pass

verbosity = 0
debug_lvl = 0


def setup(v, d):
    global verbosity, debug_lvl

    verbosity = v
    debug_lvl = d
    return


def verbo(lvl, fmt, *args):
    if verbosity >= lvl:
        sys.stderr.write(fmt % args + '\n')
    return


def debug(lvl, fmt, *args):
    if debug_lvl >= lvl:
        sys.stderr.write(fmt % args + '\n')
    return


class Error(Exception):
    def __init__(self, data):
        self.data = data
        pass

    def __str__(self):
        return f'{self.data!s}'

    def __repr__(self):
        return f'{self.data!r}'

    pass


def error(data):
    debug(9, f'error: {data!s}')
    raise Error(data)


def warn(data):
    sys.stderr.write(f'warning: {data!s}\n')
    return


@click.option('-v', '--verbose', count=True)
@click.option('-d', '--debug', count=True)
@click.group()
def cli(verbose, debug):
    setup(verbose, debug)
    pass


@cli.command()
@click.option('--name', prompt='Enter Zwift username', help='Zwift username')
@click.password_option(help='Zwift password')
def auth(name, password):
    """Establish the authentication."""

    try:
        cl = Client(name, password)
        pr = cl.get_profile()
        pr.check_player_id()
    except Exception as e:
        error(f'Authentication failure: {e}')
        pass

    try:
        keyring.set_password('zwi.py', 'username', name)
    except keyring.errors.PasswordSetError:
        raise SystemExit('Cannot set zwi.py username')

    try:
        keyring.set_password('zwi.py', name, password)
    except keyring.errors.PasswordSetError:
        raise SystemExit('Cannot set zwi.py username+password')

    try:
        if keyring.get_password('zwi.py', 'username') != name:
            raise SystemExit('keyring username mismatch')

        if keyring.get_password('zwi.py', name) != password:
            raise SystemExit('keyring password mismatch')

        sys.exit(0)
    except keyring.errors.KeyringError as e:
        raise SystemExit('***keyring error:', e)
    pass


@cli.command()
def check():
    """Verify that we have established the authentication."""
    (cl, pr) = zwi_init()
    sys.exit(0)
    pass


@cli.command()
def clear():
    """Clear out any saved authentication information."""

    try:
        name = keyring.get_password('zwi.py', 'username')
    except keyring.errors.KeyringError as e:
        raise SystemExit('***keyring error:', e)

    try:
        keyring.delete_password('zwi.py', name)
    except keyring.errors.KeyringError as e:
        raise SystemExit('Trying to delete password: ***keyring error:', e)

    try:
        keyring.delete_password('zwi.py', 'username')
    except keyring.errors.KeyringError as e:
        raise SystemExit('Trying to delete username: ***keyring error:', e)

    return sys.exit(0)


@cli.command()
def wees():
    """Display followees who are not following me."""
    followees()
    return sys.exit(0)


@cli.command()
def wers():
    """Display followers who I am not following."""
    followers()
    return sys.exit(0)


def zwi_init():
    """Initialise communications with Zwift API."""

    try:
        name = keyring.get_password('zwi.py', 'username')
    except Exception as e:
        print('Error:', e)
        raise SystemExit(f'{e!r}: Cannot locate `username` entry -- re-run `auth`.')

    if name is None:
        raise SystemExit('Error: no `username` has been specified -- re-run `auth`.')

    try:
        password = keyring.get_password('zwi.py', name)
    except Exception as e:
        print('Error:', e)
        raise SystemExit(f'{e!r} Cannot locate `password` entry for user {name} -- re-run `auth`.')

    try:
        cl = Client(name, password)
        pr = cl.get_profile()
        pr.check_player_id()
        print('player_id:', pr.player_id)
        return cl, pr
    except Exception as e:
        print('Error:', e)
        raise SystemExit('Authentication failure for user {name}.')
    pass


def followees():
    count = 0
    usr = ZwiUser()
    for r in usr.wees:
        d = dict(zip(usr.cols, r))
        count += 1
        boo = (d['followeeStatusOfLoggedInPlayer'] != d['followerStatusOfLoggedInPlayer'])

        if verbosity > 0:
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

        if verbosity > 0:
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


class DataBase(object):
    cache = {}  # DB universe

    def __init__(self, path=None, reset=False):
        self._path = path = DataBase.db_path(path)
        self._cur = None

        debug(2, f'init {self=} {self._path=} {DataBase.cache=}')

        if path in DataBase.cache:
            if reset:
                del DataBase.cache[path]
            else:
                raise Error(f'Programming error: {path} already exists in cache.')
            pass

        self._db = DataBase.__db_connect(path, reset)
        super().__init__()

        DataBase.cache[path] = self
        pass

    def __del__(self):
        debug(2, f'del {self=} {self._path=} {DataBase.cache=}')
        if self._path in DataBase.cache:
            del DataBase.cache[self._path]
            pass

    @staticmethod
    def db_path(path=None):
        """Return the path name."""
        if path is None:
            zdir = os.getenv('HOME') + '/.zwi/'
            path = zdir + 'zwi.db'
            if not os.path.isdir(zdir):
                try:
                    os.mkdir(zdir)
                except Exception as e:
                    print(f'Cannot create database directory: {zdir}')
                    print(f'{e}')
                    raise SystemExit(f'Cannot create {zdir}')
                pass
            pass
        return path

    @staticmethod
    def __db_connect(path, reset=False):
        """Setup DB for access."""

        if reset and os.path.isfile(path):
            try:
                os.remove(path)
            except Exception as e:
                # print(f'Error: {e}')
                raise e
            pass

        if reset or path not in DataBase.cache:
            try:  # first, try to create the DB
                db = sq.connect(path)
            except Exception as e:
                raise e
            DataBase.cache[path] = db
            pass
        return DataBase.cache[path]

    @classmethod
    def db_connect(cls, path=None, reset=False, drop=False):
        """Connect to a database."""
        path = cls.db_path(path)
        if path not in cls.cache:
            return DataBase(path, reset)
        else:
            return cls.cache[path]
        pass

    @property
    def db(self):
        return self._db

    @property
    def path(self):
        return self._path

    @property
    def cursor(self):
        if not self._cur:
            self._cur = self._db.cursor()
        return self._cur

    def table_exists(self, name):
        """Query if table exists in DB."""
        sel = f'''SELECT name FROM sqlite_master WHERE type='table' AND name='{name}';'''
        res = self.execute(sel)
        for tup in res.fetchall():
            # print(f'{type(tup)=} {isinstance(tup, tuple)=}')
            if isinstance(tup, tuple):
                for t in tup:
                    if t == name:
                        debug(2, f'{res=} {tup=} {t=} {t==name=}')
                        return True
                    pass
                pass
            pass
        debug(2, f'{res=} {name in res=}')
        return False

    def execute(self, exe):
        debug(2, f'{exe}')
        try:
            return self.cursor.execute(exe)
        except Exception as e:
            debug(2, f'{exe}')
            raise Error(f'execute({exe} => {e}')
        pass

    def drop_table(self, name):
        self.execute(f'DROP TABLE IF EXISTS {name};')
        return

    def create_table(self, name, cols):
        exe = f"CREATE TABLE IF NOT EXISTS {name}({', '.join(cols)});"
        self.execute(exe)
        return

    def row_insert(self, name, cols, vals):
        debug(2, f'{cols=}')
        debug(2, f'{vals=}')
        exe = f'''INSERT INTO {name} ({', '.join(cols)}) VALUES({', '.join(vals)});'''
        self.execute(exe)
        self.commit()
        return

    def table_rows(self, name, cols, arraysize=200):
        """Return a generator for the specified rows in the named table."""
        sel = ', '.join(f'{a}' for a in cols)
        r = self.execute(f'SELECT {sel} FROM {name} ORDER BY rowid')

        def gen():
            while True:
                ar = r.fetchmany(arraysize)

                if not ar:
                    break
                for e in ar:
                    yield e
                    pass
                pass
            pass

        return gen

    def commit(self):
        return self.db.commit()

    def close(self):
        self._cur.close()
        del self._cur
        self._cur = None
        self._db.close()
        del self._db
        self._db = None

    pass


class ZwiBase(object):
    """base class for Zwi @dataclass objects."""

    def traverse(self, fun, arg):
        """traverse structure built by the default __init__."""
        for x in fields(self):
            if x.type in (int, str, bool):
                fun(self, x, arg)
            elif isinstance(x.type(), ZwiBase):
                fun(self, x, arg)
                pass
            pass
        return arg

    @staticmethod
    def from_dict(f, x, arg):
        """Assign values from a supplied dict()."""
        if x.name in arg:
            debug(2, f'{x.name=} {x.type=} {arg[x.name]=}')
            if x.type in (int, bool):
                setattr(f, x.name, arg[x.name])
            elif x.type is str:
                setattr(f, x.name, arg[x.name])
            elif isinstance(x.type(), ZwiBase):
                # we expect that f.<value> here is a suitable dict
                f0 = getattr(f, x.name)
                if f0 is not None and x.name in arg:
                    debug(2, f'dict: {f0=} {arg[x.name]=}')
                    f0.traverse(ZwiBase.from_dict, arg[x.name])
                else:
                    raise SystemExit(f'oops')
                pass
            else:
                raise SystemExit(f'Unexpected type: {x.type=}')
            pass
        return arg

    @staticmethod
    def to_dict(f, x, arg):
        """Assing values to a supplied dict().
        Does not construct the dict or add any missing fields."""
        if x.name in arg:
            # print(f'{x.name=} {x.type=} {arg[x.name]=}')
            if x.type in (int, bool):
                arg[x.name] = getattr(f, x.name)
            elif x.type is str:
                arg[x.name] = getattr(f, x.name)
            elif isinstance(x.type(), ZwiBase):
                # we expect that self.<value> here is a suitable dict
                f0 = getattr(f, x.name)
                if f0 is not None:
                    debug(2, f'dict: {f0=} {arg[x.name]=}')
                    f0.traverse(f.to_dict, arg[x.name])
                    pass
                pass
            else:
                raise SystemExit(f'Unexpected type: {x.type=}')
            pass
        return arg

    @staticmethod
    def from_seq(f, x, arg):
        """Assign values from a sequence.
        We perform a depth-first traversal, and pop successive values from the sequence."""
        # print(f'{x.name=} {x.type=}')
        if x.type in (int, bool):
            setattr(f, x.name, arg.pop())
        elif x.type is str:
            setattr(f, x.name, arg.pop())
        elif isinstance(x.type(), ZwiBase):
            # decide what we need the recursion to do:
            f0 = getattr(f, x.name)
            debug(2, f'from_seq: {x.name=} {f0}')
            if f0 is not None:
                f0.traverse(f0.from_seq, arg)
                pass
            raise SystemExit('logic error')
        else:
            raise SystemExit(f'Unexpected type: {x.type=}')
        return arg

    pass


@dataclass
class ZwiFollowers(ZwiBase):
    followerId: int = 0
    followeeId: int = 0
    status: str = ''
    isFolloweeFavoriteOfFollower: bool = False

    @dataclass
    class FollowerProfile(ZwiBase):
        publicId: str = ''
        firstName: str = ''
        lastName: str = ''
        male: bool = True
        imageSrc: str = ''
        imageSrcLarge: str = ''
        playerType: str = ''
        countryAlpha3: str = ''
        countryCode: int = 0
        useMetric: bool = True
        riding: bool = False

        @dataclass
        class Privacy(ZwiBase):
            approvalRequired: bool = False
            displayWeight: bool = False
            minor: bool = False
            privateMessaging: bool = False
            defaultFitnessDataPrivacy: bool = False
            suppressFollowerNotification: bool = False
            displayAge: bool = True
            defaultActivityPrivacy: str = ''

            pass

        privacy: Privacy = Privacy()

        @dataclass
        class SocialFacts(ZwiBase):
            followersCount: int = 0
            followeesCount: int = 0
            followeesInCommonWithLoggedInPlayer: int = 0
            followerStatusOfLoggedInPlayer: str = ''
            followeeStatusOfLoggedInPlayer: str = ''
            isFavoriteOfLoggedInPlayer: bool = True
            pass

        socialFacts: SocialFacts = SocialFacts()
        worldId: int = 0
        enrolledZwiftAcademy: bool = False
        playerTypeId: int = 0
        playerSubTypeId: int = 0
        currentActivityId: int = 0
        likelyInGame: bool = False
        pass

    profile: FollowerProfile = FollowerProfile()

    addDate: str = f'''{datetime.now().isoformat(timespec='minutes')}'''
    delDate: str = 'not yet'

    @classmethod
    def wers(cls, data):
        """Init a followers-type entry."""

        if isinstance(data, dict):
            # assumed to be per the Zwift format.
            assert 'followerProfile' in data
            data['profile'] = data['followerProfile']
            e = ZwiFollowers()
            e.traverse(ZwiBase.from_dict, data)
            return e
        raise Exception(f'funny type of {data!r}')

    @classmethod
    def wees(cls, data):
        """Init a followees-type entry."""

        if isinstance(data, dict):
            # assumed to be per the Zwift format.
            assert 'followeeProfile' in data
            data['profile'] = data['followeeProfile']
            e = ZwiFollowers()
            e.traverse(ZwiBase.from_dict, data)
            return e
        raise Exception(f'funny type of {data!r}')

    @classmethod
    def column_names(cls, pk='', create=False):
        """generate the columnt list for a DB create."""
        tmap = {int: 'INT', bool: 'INT', str: 'TEXT'}

        def fun(f, x, arg):
            """Function to enumerate the column names."""
            if x.type in (int, bool, str):
                if not create:  # INSERT/SELECT usage
                    arg.append(f'{x.name}')  # .. no type
                elif x.name == pk:  # CREATE and PRIMARY
                    arg.append(f'{x.name} {tmap[x.type]} PRIMARY KEY')
                else:  # CREATE, no PRIMARY
                    arg.append(f'{x.name} {tmap[x.type]}')
            elif isinstance(x.type(), ZwiBase):
                f0 = getattr(f, x.name)
                if f0 is not None:
                    f0.traverse(fun, arg)
                    pass
                pass
            pass

        return cls().traverse(fun, list())

    def column_values(self):
        """generate the values list for a DB insert."""
        def fun(f, x, arg):
            """Function to enumerate the column values."""
            val = getattr(f, x.name)

            if x.type in (int, bool):
                if val is None:
                    val = 0
                else:
                    val = int(val)
                    pass
                arg.append(f'{val}')
            elif x.type is str:
                # We need to replace all single ' with double ''
                val = str(val).replace("'", "''")
                arg.append(f"'{val}'")
            elif isinstance(x.type(), ZwiBase):
                f0 = getattr(f, x.name)
                if f0 is not None:
                    f0.traverse(fun, arg)
                    pass
                pass
            pass
        return self.traverse(fun, list())
    pass


def get_zdir(xtra=''):
    """Establish local Zwi directory."""

    zdir = os.getenv('HOME') + '/.zwi/' + xtra
    if not os.path.isdir(zdir):
        try:
            os.mkdir(zdir)
        except Exception as e:
            print(f'Cannot create zwi directory: {zdir}')
            print(f'{e}')
            raise SystemExit(f'Cannot create {zdir}')
        pass
    return zdir


class ZwiUser(object):
    """Zwift user model."""

    def __init__(self, db=None, drop=False, update=False):
        self._db = db
        self._wers = []
        self._wees = []
        self._cols = ZwiFollowers.column_names()
        self._cl = None
        self._pr = None
        self._setup(drop, update)
        pass

    @property
    def cols(self):
        return self._cols

    @property
    def wees(self):
        return self._wees

    @property
    def wers(self):
        return self._wers
    
    def _setup(self, drop, update):
        """Syncronise with the local DB version of the world."""
        if self._db is None:  # attach to the usual DB
            self._db = DataBase.db_connect()
            pass

        if drop:
            self._db.drop_table('followers')
            self._db.drop_table('followees')
            self._db.drop_table('enum')  # XXX: not here
            pass

        self._db.create_table('followers', ZwiFollowers.column_names(create=True, pk='followerId'))
        self._db.create_table('followees', ZwiFollowers.column_names(create=True, pk='followeeId'))

        if update:  # update from Zwift?
            self.update('followers', self.wers_fac)
            self.update('followees', self.wees_fac)
            pass

        self._slurp(self._wers, 'followers')
        self._slurp(self._wees, 'followees')
        pass

    def _slurp(self, cache, tab):
        """Slurp in the table data."""
        g = self._db.table_rows(tab, self._cols)
        count = 0
        for r in g():
            cache.append(r)
            count = count + 1
            if count <= 10 and verbosity >= 2:
                verbo(3, f'{r=}')
            elif verbosity >= 1:
                print(f'\rslurped {tab}: {count}', end='')
                pass
            pass
        verbo(1, '')
        pass

    def update(self, tab, factory):
        if self._pr is None:
            self._cl, self._pr = zwi_init()
            pass

        vec = []
        start = 0
        while True:
            fe = self._pr.request.json(f'/api/profiles/{self._pr.player_id}/{tab}?start={start}&limit=200')
            if len(fe) == 0:
                break

            for f in fe:
                start += 1
                vec.append(f)
                pass
            if verbosity >= 1:
                print(f'\rprocessed {tab}: {start}', end='')
                pass
            pass
        verbo(1, '')

        # I want to add these into the DB in historical order.
        # It appears that more recent followers are returned first above.
        vec.reverse()

        start = 0
        for v in vec:
            w = factory(v)
            self._db.row_insert(tab, w.column_names(), w.column_values())
            start += 1
            if verbosity >= 1:
                print(f'\rprocessed {tab}: {start}', end='')
                pass
            pass
        verbo(1, '')
        return

    def wers_fac(self, v):
        o = ZwiFollowers.wers(v)
        self._wers.append(o)
        return o

    def wees_fac(self, v):
        o = ZwiFollowers.wees(v)
        self._wees.append(o)
        return o

    pass


@cli.command()
def oldgui():
    """Play with Qt to see if can use....
    I will be removing this soon.
    """
    try:
        import PyQt5
        from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTableWidget
        from PyQt5.QtCore import (pyqtSignal, QPointF, QRect, QSize, Qt,
                                  QRunnable, QThreadPool, QMutex, QSemaphore)
        from PyQt5.QtGui import (QPainter, QPolygonF, QIcon, QPixmap, QBrush, QPen, QColor, QFont)
        from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QStyle,
                                     QStyledItemDelegate, QTableWidget, QTableWidgetItem, QWidget,
                                     QGridLayout,
                                     QMainWindow,
                                     QStyleOptionViewItem)
        import shutil
        import urllib.request
        import ssl
    except Exception as e:
        print('import error', e)
        print('pip3 install pyqt5')
        sys.exit(1)
        pass

    class ZwiView(QWidget):
        editingFinished = pyqtSignal()

        def __init__(self, parent=None):
            super(ZwiView, self).__init__(parent)

            self.setMouseTracking(True)
            self.setAutoFillBackground(True)
            pass

        def sizeHint(self):
            a = QWidget.sizeHint(self)
            a.setHeight(a.height() + 75)
            a.setWidth(a.width() + 100)
            print(f'sizeHint: {a.height()=}, {a.width()=}')
            return a

        def paintEvent(self, event):
            painter = QPainter(self)
            # print(f'paintEvent {event=}')
            return

        def mouseMoveEvent(self, event):
            print(f'mouseMove {event=}')
            return

        def mouseReleaseEvent(self, event):
            print(f'mouseRelease {event=}')
            self.editingFinished.emit()
            return

        pass

    class ZwiDelegate(QStyledItemDelegate):
        def __init__(self, tab, *args, **kwargs):
            super(ZwiDelegate, self).__init__(*args, **kwargs)        
            self._tab = tab
            pass

        def paint(self, painter, option, index):
            # print(f'paint {option=} {index=} {index.row()=} {index.column()=}')
            if index.column() == 0:
                x, y, w, h = option.rect.x(), option.rect.y(), option.rect.width(), option.rect.height()
                # print(f'option: {x},{y} {w},{h}')
                self.initStyleOption(option, index)
                super(ZwiDelegate, self).paint(painter, option, index)
                painter.save()
                pen = QPen(QColor("black"))
                qr = QRect(option.rect)
                qr.setWidth(pen.width())
                painter.setPen(pen)
                painter.drawRect(qr)
                painter.restore()
            else:
                super(ZwiDelegate, self).paint(painter, option, index)
            return

        def sizeHint(self, option, index):
            if True and index.column() == 0:
                # seems to set the with
                return QSize(256, 256)
            size = super(ZwiDelegate, self).sizeHint(option, index)
            if False and index.column() == 0:
                # does not help
                print(f'sizeHint: {option=} {index=} {index.row()=} {index.column()=}')
                total_width = self._tab.viewport().size().width()
                calc_width = size.width()
                for i in range(self._tab.columnCount()):
                    if i != index.column():
                        option_ = QStyleOptionViewItem()
                        index_  = self._tab.model().index(index.row(), i)
                        self.initStyleOption(option_, index_)
                        size_ = self.sizeHint(option_, index_)
                        calc_width += size_.width()
                        pass
                    pass
                if calc_width < total_width:
                    size.setWidth(size.width() + total_width - calc_width)
            return size

        def createEditor(self, parent, option, index):
            """Do not create editor: all are read-only."""
            return None

        def setEditorData(self, editor, index):
            print(f'setEditorData: {self=} {editor=} {index=}')
            super(ZwiDelegate, self).setEditorData(editor, index)
            return

        def setModelData(self, editor, model, index):
            print(f'setModeData: {self=} {editor=} {index=}')
            super(ZwiDelegate, self).setModelData(editor, model, index)
            return

        def commitAndCloseEditor(self):
            editor = self.sender()
            self.commitData.emit(editor)
            self.closeEditor.emit(editor)
            return

        pass

    # logging.basicConfig(format="%(message)s", level=logging.INFO)

    class ImageCache(QRunnable):
        def __init__(self, sig):
            super().__init__()
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

        def load(self, key, widget, tab):
            """Load an image into the cache."""
            self._mux.lock()
            if key in self._cache:
                icon = self._cache[key]
            else:
                icon = QIcon()
                self._cache[key] = icon

                self._queue.insert(0, (key, widget, icon, tab))
                self._requ.release()
                if self._nthreads == 0:
                    self._terminate = False
                    self._pool.start(self)
                    self._nthreads = 1
                    pass
                pass
            self._mux.unlock()
            return icon

        def run(self):
            """Thread function."""
            # print(f'running: {self=}')
            while True:
                self._requ.acquire()
                self._mux.lock()
                if self._terminate:
                    # print(f'{self=} {self._terminate=} {self._nthreads=}')
                    self._terminate = False
                    self._nthreads = 0
                    assert len(self._queue) == 0
                    self._mux.unlock()
                    return

                wrk = self._queue.pop()
                self._mux.unlock()

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
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context

        def update(self):
            self._mux.lock()
            while len(self._done) > 0:
                wrk = self._done.pop()
                self._mux.unlock()

                key, wid, tab = wrk[0], wrk[1], wrk[3]
                icon = self._cache[key]
                icon.addFile(f'''{self._path}/{key.split('/')[-1]}''', size=QSize(128, 128))
                # icon.Mode = QIcon.Normal
                wid.setIcon(icon)
                if False:
                    # turn off for now
                    px = QPixmap(f'''{self._path}/{key.split('/')[-1]}''')
                    wid.setData(Qt.DecorationRole, px)
                    # tab.resizeColumnToContents(0)
                    pass
                wid.update()

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

    app = QApplication([])
    usr = ZwiUser()

    class MyTable(QTableWidget):
        sig = pyqtSignal(int, name='results')

        def __init__(self, r, c, parent=None):
            super(MyTable, self).__init__(r, c, parent)
            self.sig.connect(self.handle)
            self.setIconSize(QSize(256, 256))
            pass

        def handle(self, index):
            icache.update()
            pass

        # def cellActivated(self, row, col):
        #    print(f'cell active: {row} {col}')

        def itemClicked(self, item):
            print(f'clicked: {item}')
            pass
        pass


    tab = MyTable(len(usr.wers), 5)
    
#delegate = ResizeDelegate(table, 0)
#table.setItemDelegate(delegate)
#table.resizeColumnsToContents()

    tab.setItemDelegate(ZwiDelegate(tab))
    tab.setEditTriggers(
        QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
    tab.setSelectionBehavior(QAbstractItemView.SelectItems)

    headerLabels = ("", "First Name", "Last Name", "FollowerStatus", "FolloweeStatus")
    tab.setHorizontalHeaderLabels(headerLabels)

    icache = ImageCache(tab.sig)
    fg = QBrush(QColor('yellow'))
    bg = QBrush(QColor('black'))
    font = QFont()
    font.setPointSize(16)

    class MugShot(QTableWidgetItem):
        def __init__(self, tab, *args, **kwargs):
            super(MugShot, self).__init__(*args, **kwargs)
            self._tab = tab
            self.setForeground(fg)
            self.setBackground(bg)
            self.setFont(font)

        def update(self):
            self._tab.update()
            pass

        def clone(self):
            c = MugShot(self._tab)
            return c

        def keyPressEvent(self, event):
            key = event.key()
            print(f'keyPress: {event=} {key=}')

            if key == Qt.Key_Return or key == Qt.Key_Enter:
                print('clicked enter')
                pass
            pass

        pass

    class RowCol(QTableWidgetItem):
        def __init__(self, *args, **kwargs):
            super(RowCol, self).__init__(*args, **kwargs)
            self.setForeground(fg)
            self.setBackground(bg)
            self.setFont(font)
            pass
        
        def clone(self):
            c = RowCol()
            return c

        def keyPressEvent(self, event):
            key = event.key()
            print(f'keyPress: {event=} {key=}')

            if key == Qt.Key_Return or key == Qt.Key_Enter:
                print('clicked enter')
                pass
            pass

        pass


    row = 0
    for r in usr.wers:
        d = dict(zip(usr.cols, r))

        item0 = MugShot(tab)
        icon = icache.load(d['imageSrc'], item0, tab)
        item0.setIcon(icon)
        item0.setSizeHint(QSize(128, 128))

        item1 = RowCol(d['firstName'])
        item2 = RowCol(d['lastName'])
        item3 = RowCol(d['followerStatusOfLoggedInPlayer'])
        item4 = RowCol(d['followeeStatusOfLoggedInPlayer'])

        tab.setItem(row, 0, item0)
        tab.setItem(row, 1, item1)
        tab.setItem(row, 2, item2)
        tab.setItem(row, 3, item3)
        tab.setItem(row, 4, item4)
        tab.setRowHeight(row, 256)
        row += 1
        pass

    tab.resizeColumnsToContents()
    tab.resize(1024, 1024)
    tab.show()

    label = PyQt5.QtWidgets.QLabel()
    for dname, subd, files in os.walk(get_zdir('.image-cache')):
        while True:
            for f in files:
                px = QPixmap(f)
                label.resize(px.size())
                label.setPixmap(px)
                label.show()
                break
                pass
            break
            pass
        pass

    class MyBut(QWidget):
        def __init__(self, texts, parent):
            QWidget.__init__(self, parent)

            gridLayout = QGridLayout()
            for i in range(0, texts.size()):
                text = texts[i]
                button = QPushButton(text)
                # ?? connect(button, QPushButton.clicked, [self, text] { clicked(text); })
                gridLayout.addWidget(button, i / 3, i % 3)

            setLayout(gridLayout)
            pass
        pass

    MyBut(['1','2','3'], label)

    QApplication.processEvents()
    sys.exit(app.exec_())
    pass


@cli.command()
def test():
    """Perform some modicum of internal tests."""
    try:
        raise Exception('yo!')
    except Exception as e:
        print(f'{e!r}: oops!')
        pass

    db0 = DataBase.db_connect()
    db1 = DataBase.db_connect('/tmp/zwi_test.db', reset=True)
    db2 = DataBase.db_connect('/tmp/zwi_test.db', reset=True)
    db3 = DataBase.db_connect()

    assert db0 == db3
    assert db2 != db3

    print(f"{db1=} {db1.table_exists('followers')=}")
    print(f"{db1=} {db1.table_exists('followees')=}")

    db1.close()
    pass


@cli.command()
def reset():
    """Reset the database, refresh followers/followees data."""
    db = DataBase.db_connect(reset=True)
    ZwiUser(db, update=True)

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
        print('import error', e)
        print('pip3 install pyqt5')
        sys.exit(1)
        pass

    qtcreator_file  = "zwi_ui_v0.ui"
    Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

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

            self.butNext.clicked.connect(self.doNext)
            self.butPrev.clicked.connect(self.doPrev)
            self.butQuit.clicked.connect(self.doQuit)

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

            self.sb.valueChanged.connect(self.sbValueChanged)

            self._usr = ZwiUser()
            self._icache = ImageCache(self.sig)
            self.switch('wers')
            pass

        def sbValueChanged(self, val):
            if val < self._max:
                self._idx = val
                pass
            self.refresh(0)
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
                self._timer = NOne
                pass
            pass

        def doNext(self):
            if self._timer:
                i = self._timer.interval()
                self._timer.setInterval(i*2)
                return
            self.refresh(1)
            pass

        def doPrev(self):
            if self._timer:
                i = self._timer.interval()
                self._timer.setInterval(100 + int(i/2))
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
            f = QMessageBox(parent=self)
            f.setText('Use `zwi clear` to reset the Zwift user authentication.')
            f.exec_()
            pass
            
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
        
        def refresh(self, delta=0):
            self._idx += delta
            if self._idx > self._max:
                self._idx = 0
            elif self._idx < 0:
                self._idx = self._max
                pass
                
            self.sb.setValue(self._idx)
            
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

    
if __name__ == '__main__':
    try:
        cli()
        sys.exit(0)
    except Exception as e:
        debug(2, f'{type(e)=}\n{e!r}')
        print(f'{e}')
        if debug_lvl > 0:
            raise Exception('oops!') from e
        sys.exit(1)
