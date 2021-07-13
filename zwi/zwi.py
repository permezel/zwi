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
import threading
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

    name = None

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
    for r in usr._wers:
        d = dict(zip(usr._cols, r))
        count += 1
        boo = (d['followeeStatusOfLoggedInPlayer'] != d['followerStatusOfLoggedInPlayer'])

        if verbosity > 0:
            # dump out entire list
            print('{:4d}{}{} {}\t{} {}'.format(count, [' ', '*'][boo]
                                               , d['followeeStatusOfLoggedInPlayer']
                                               , d['followerStatusOfLoggedInPlayer']
                                               , d['firstName'], d['lastName']))
        elif boo:
            # disply only those whos soc status match
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
    for r in usr._wers:
        d = dict(zip(usr._cols, r))
        count += 1
        boo = (d['followeeStatusOfLoggedInPlayer'] != d['followerStatusOfLoggedInPlayer'])

        if verbosity > 0:
            print('{:4d}{}{} {}\t{} {}'.format(count, [' ', '*'][boo]
                                               , d['followeeStatusOfLoggedInPlayer']
                                               , d['followerStatusOfLoggedInPlayer']
                                               , d['firstName'], d['lastName']))
        elif boo:
            # disply only those whos soc status match
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
        rows = usr._wers
    elif wees:
        rows = usr._wees
    else:
        raise SystemExit('No table selected.')
        pass
    
    with sys.stdout as out:
        writer = csv.DictWriter(out, fieldnames=usr._cols)
        writer.writeheader()
        for r in rows:
            d = dict(zip(usr._cols, r))
            writer.writerow(d)
            pass
        pass
    pass


class EnumCache(object):
    """Currently not using the enum cache."""
    def __init__(self, db, name='enum'):
        super().__init__()
        self._db = db
        self._name = name
        self._enumv = {}  # _enum['class']['name'] = val
        self._enums = {}  # _enum['class'][val] = 'name'
        self._setup()
        pass

    def enum_set(self, c, k, v):
        """map value thru enum cache."""
        if not c in self._enumv:
            self._enumv[c] = {}
            self._enums[c] = {}
            pass

        if k in self._enumv[c]:
            assert self._enumv[c][k] == v
            assert self._enums[c][v] == k
        else:
            self._db.execute(f'''INSERT INTO {self._name} VALUES('{c}', '{k}', {v});''')
            self._db.commit()
            self._enumv[c][k] = v
            self._enums[c][v] = k
            pass
        return v

    def enum_get(self, c, k):
        """If `c[k]` is not currently in the cache, we add it."""
        if not c in self._enumv:
            self._enumv[c] = {}
            self._enums[c] = {}
            pass
        if not k in self._enumv[c]:
            return self.enum_set(c, k, len(self._enumv[c]))
        return self._enumv[c][k]

    def enum_str(self, c, v):
        return self._enums[c][v]

    def _setup(self):
        """Establish table in DB if required.  Cache any extant values."""
        self.gen_tables()
        self.sync_cache()
        pass

    def table_exists(self):
        debug(2, f'enum_table_exists({self=}, {self._name=}, {self._db=})')
        return self._db.table_exists(self._name)

    def gen_tables(self, drop=False):
        """Generate the ENUM table."""
        debug(2, f'gen_table({self=}, {self._name=}, {self._db=}, {drop=})')

        if drop:
            self._db.drop_tables()
            pass
        self._db.execute(
            f'''CREATE TABLE IF NOT EXISTS {self._name} (cat INT, name TEXT, val INT, UNIQUE(cat, name), PRIMARY KEY(cat, val)) WITHOUT ROWID;''')
        self._db.commit()
        pass

    def sync_cache(self):
        try:
            res = self._db.execute(f'''SELECT * FROM {self._name};''')
        except Exception as e:
            print(f'{e=}')
            res = []
            pass

        for r in res:
            debug(2, f'{res=}')
            (c, k, v) = r
            if c in self._enumv and k in self._enumv[c]:
                assert self._enumv[c][k] == v
            else:
                if c not in self._enumv:
                    self._enumv[c] = {}
                    pass
                self._enumv[c][k] = v
                pass
            pass
        return

    pass


class DataBase(EnumCache):
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
        self.execute('PRAGMA foreign_keys=ON;')
        super().__init__(self._db)

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
        verbo(1, f'{exe}')
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
        verbo(1, f'{cols=}')
        verbo(1, f'{vals=}')
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
                    raise SysException(f'oops')
                pass
            else:
                raise SysException(f'Unexpected type: {x.type=}')
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
                raise SysException(f'Unexpected type: {x.type=}')
            pass
        return arg

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
            raise SysException('logic error')
        else:
            raise SysException(f'Unexpected type: {x.type=}')
        return arg
    
    pass


@dataclass
class ZwiFollowers(ZwiBase):
    # id:					int = 0
    followerId:				int = 0
    followeeId:				int = 0
    status:				str = ''
    isFolloweeFavoriteOfFollower:	bool = False

    @dataclass
    class FollowerProfile(ZwiBase):
        # id:			int = 0
        publicId:		str = ''
        firstName:		str = ''
        lastName:		str = ''
        male:			bool = True
        imageSrc:		str = ''
        imageSrcLarge:		str = ''
        playerType:		str = ''
        countryAlpha3:		str = ''
        countryCode:		int = 0
        useMetric:		bool = True
        riding:			bool = False

        @dataclass
        class Privacy(ZwiBase):
            approvalRequired:			bool = False
            displayWeight:			bool = False
            minor:				bool = False
            privateMessaging:			bool = False
            defaultFitnessDataPrivacy:		bool = False
            suppressFollowerNotification:	bool = False
            displayAge:				bool = True
            defaultActivityPrivacy:		str = ''

            pass


        privacy: Privacy = Privacy()

        @dataclass
        class SocialFacts(ZwiBase):
            #profileId:				int = 0
            followersCount:			int = 0
            followeesCount:			int = 0
            followeesInCommonWithLoggedInPlayer:int = 0
            followerStatusOfLoggedInPlayer:	str = ''
            followeeStatusOfLoggedInPlayer:	str = ''
            isFavoriteOfLoggedInPlayer:		bool = True
            pass


        socialFacts: SocialFacts = SocialFacts()
        worldId:		int = 0
        enrolledZwiftAcademy:	bool = False
        playerTypeId:		int = 0
        playerSubTypeId:	int = 0
        currentActivityId:	int = 0
        likelyInGame:		bool = False
        pass

    profile: FollowerProfile = FollowerProfile()

    addDate:			str = f'''{datetime.now().isoformat(timespec='minutes')}'''
    delDate:			str = 'not yet'

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
                if not create:			# INSERT/SELECT usage
                    arg.append(f'{x.name}')	# .. no type
                elif x.name == pk:		# CREATE and PRIMARY
                    arg.append(f'{x.name} {tmap[x.type]} PRIMARY KEY')
                else:				# CREATE, no PRIMARY
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
        tmap = {int: 'INT', bool: 'INT', str: 'TEXT'}
        
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

        print
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

    def _setup(self, drop, update):
        """Syncronise with the local DB version of the world."""
        if self._db is None:	# attach to the usual DB
            self._db = DataBase.db_connect()
            pass

        if drop:
            db.drop_table('followers')
            db.drop_table('followees')
            db.drop_table('enum')	# XXX: not here
            pass

        self._db.create_table('followers', ZwiFollowers.column_names(create=True, pk='followerId'))
        self._db.create_table('followees', ZwiFollowers.column_names(create=True, pk='followeeId'))

        if update:  # update from Zwift?
            usr.update('followers', usr.wers_fac)
            usr.update('followees', usr.wees_fac)
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
                verbo(2, f'{r=}')
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
            fe = self._pr.request.json(f'/api/profiles/{self._pr.player_id}/{tab}?start={start}&limit=50')
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
            verbo(1, f'\rprocessed {tab}: {start}', end='')
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
def gui():
    """Play with Qt to see if can use...."""
    try:
        import PyQt5
        from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTableWidget
        from PyQt5.QtCore import pyqtSignal, QPointF, QRect, QSize, Qt, QRunnable, QThreadPool, QMutex, QSemaphore
        from PyQt5.QtGui import QPainter, QPolygonF, QIcon, QPixmap, QBrush, QPen, QColor
        from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QStyle,
                                     QStyledItemDelegate, QTableWidget, QTableWidgetItem, QWidget)
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

        def __init__(self, parent = None):
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
        def paint(self, painter, option, index):
            # print(f'paint {option=} {index=} {index.row()=} {index.column()=}')
            if index.column() == 0:
                x,y,w,h = option.rect.x(), option.rect.y(), option.rect.width(), option.rect.height()
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
            # print(f'sizeHint: {option=} {index=} {index.row()=} {index.column()=}')
            if index.column() == 0:
                return QSize(256, 256)
            return super(ZwiDelegate, self).sizeHint(option, index)

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
            self._queue = []
            self._done = []
            self._cache = {}
            self._context = self._ssl_kluge()
            self._threads = list()
            self._path =  get_zdir('.image-cache')
            self._mux  = QMutex()
            self._requ = QSemaphore()
            self._resp = QSemaphore()
            self._pool = QThreadPool.globalInstance()
            self._sig = sig
            self._terminate = False
            self._nthreads = 0
            pass

        def load(self, key, widget):
            """Load an image into the cache."""
            self._mux.lock()
            if key in self._cache:
                icon = self._cache[key]
            else:
                icon = QIcon()
                self._cache[key] = icon

                self._queue.insert(0, (key, widget, icon))
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
                if key == 'None' or not 'http' in key:
                    continue	# some are None???

                path = f'''{self._path}/{key.split('/')[-1]}'''
                if not os.path.isfile(path):
                    self._fetch(key)
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

        def _ssl_kluge(self):
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

                key, wid = wrk[0], wrk[1]
                icon = self._cache[key]
                icon.addFile(f'''{self._path}/{key.split('/')[-1]}''', size=QSize(128,128))
                # icon.Mode = QIcon.Normal
                wid.setIcon(icon)
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
                del self._cache[key]
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

        def __init__(self, r, c, parent = None):
            super(MyTable, self).__init__(r, c, parent)
            self.sig.connect(self.handle)
            self.setIconSize(QSize(256,256))
            pass

        def handle(self, index):
            icache.update()
            pass
        pass

    tab = MyTable(len(usr._wers), 5)
    tab.setItemDelegate(ZwiDelegate())
    tab.setEditTriggers(
        QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
    tab.setSelectionBehavior(QAbstractItemView.SelectRows)

    headerLabels = ("", "First Name", "Last Name", "FollowerStatus", "FolloweeStatus")
    tab.setHorizontalHeaderLabels(headerLabels)

    icache = ImageCache(tab.sig)

    class MugShot(QTableWidgetItem):
        def __init__(self, tab, *args, **kwargs):
            super(MugShot, self).__init__(*args, **kwargs)
            self._tab = tab

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
    
    row = 0
    for r in usr._wers:
        d = dict(zip(usr._cols, r))
        

        item0 = MugShot(tab)
        icon = icache.load(d['imageSrc'], item0)
        item0.setIcon(icon)
        item0.setSizeHint(QSize(128, 128))

        item1 = QTableWidgetItem(d['firstName'])
        item2 = QTableWidgetItem(d['lastName'])
        item3 = QTableWidgetItem(d['followerStatusOfLoggedInPlayer'])
        item4 = QTableWidgetItem(d['followeeStatusOfLoggedInPlayer'])

        tab.setItem(row, 0, item0)
        tab.setItem(row, 1, item1)
        tab.setItem(row, 2, item2)
        tab.setItem(row, 3, item3)
        tab.setItem(row, 4, item4)
        row += 1
        pass

    tab.resizeColumnsToContents()
    tab.resize(1024, 1024)
    tab.show()

    QApplication.processEvents()
    sys.exit(app.exec_())
    pass


@cli.command()
def devel():
    """Try out some devel options."""

    db = DataBase.db_connect()
    usr = ZwiUser(db, drop=False, update=False)

    if True: return

    #db1.table_exists('zwi')
    #db1.create_table('zwi', f)
    #db1.row_insert('zwi', f)

    init = asdict(f)
    
    f.traverse(ZwiBase.from_dict, Followers.template)
    db1.row_insert('zwi', f)

    f.traverse(ZwiBase.from_dict, __wees)
    db1.row_insert('zwi', f)

    d = f.traverse(ZwiBase.to_dict, init)
    print(f'{f=}')
    print(f'{d=}')

    def fun(f, x, arg):
        if x.type in (int, bool, str):
            arg.append(x.name)
        elif isinstance(x.type(), ZwiBase):
            f0 = eval(f'f.{x.name}')
            if f0 is not None:
                f0.traverse(fun, arg)
                pass
            pass
        pass

    cols = f.traverse(fun, [])
    pass

@cli.command()
def test():
    """Perform some modicum of internal tests."""

    try:
        raise Exception('yo!')
    except Exception as e:
        print(f'{e!r}: oops!')
        pass

    f = ZwiFollowers()
    f.traverse(ZwiBase.from_dict, __wees)
    f.traverse(ZwiBase.from_dict, __wers)

    db0 = DataBase.db_connect()
    db1 = DataBase.db_connect('/tmp/zwi_test.db', reset=True)
    db2 = DataBase.db_connect('/tmp/zwi_test.db', reset=True)
    db3 = DataBase.db_connect()

    assert db0==db3
    assert db2!=db3

    print(f"{db1=} {db1.table_exists('followers')=}")
    print(f"{db1=} {db1.table_exists('followees')=}")

    setup(1, 1)
    _gui(db0)
    db1.close()

    pass

def db_setup(reset=False):
    """Generate the initial database.
    Currently, I only snarf in the followers table.
    Currently, I do not handle updates."""

    db = DataBase.db_connect(reset=reset)

    nascent = not db.table_exists('followers')
    if nascent:
        Followers.gen_table(db)

        cl, pr = zwi_init()
        vec = []
        start = 0

        while True:
            fe = pr.request.json('/api/profiles/{}/followers?start={}&limit=200'.format(pr.player_id, start))
            if len(fe) == 0:
                break

            for f in fe:
                start += 1
                vec.append(f)
                pass
            print('\rprocessed followers: {:d}'.format(start), end='')
            pass
        print('')

        # I want to add these into the DB in historical order.
        # It appears that more recent followers are returned first above.
        vec.reverse()

        start = 0
        for v in vec:
            w = Followers(v)
            w.db_insert(db)
            start += 1
            print('\rprocessed followers: {:d}'.format(start), end='')
            del w
            pass
        print('')
        db.commit()
        pass

    # determine max column widths
    Followers.db_colmax(db)

    return db


@cli.command()
def reset():
    """Reset the database, refresh followers/followees data."""

    db = DataBase.db_connect(reset=True)
    usr = ZwiUser(db, update=True)

    return 0


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
