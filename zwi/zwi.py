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
import sqlite3 as sq
from datetime import datetime, date, time        

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
    if verbosity >= lvl: sys.stderr.write(fmt % args + '\n')
    return

def debug(lvl, fmt, *args):
    if debug_lvl >= lvl: sys.stderr.write(fmt % args + '\n')
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
    '''Establish the authentication.'''

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
    '''Verify that we have established the authentication.'''
    (cl, pr) = zwi_init()
    sys.exit(0)
    pass

@cli.command()
def clear():
    '''Clear out any saved authentication information.'''

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
    '''Display followees who are not following me.'''
    followees()
    return sys.exit(0)

@cli.command()
def wers():
    '''Display followers who I am not following.'''
    setup(verbose, debug)
    followers()
    return sys.exit(0)
    
def zwi_init():
    '''Initialise communications with Zwift API.'''

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
        return (cl, pr)
    except Exception as e:
        print('Error:', e)
        raise SystemExit('Authentication failure for user {name}.')
    pass

def followees():
    count = 0
    '''
    while True:
        fe = pr.request.json('/api/profiles/{}/followees?start={}&limit=200'.format(pr.player_id, start))
        if len(fe) == 0:
            break
        
        for f in fe:
            count += 1
            fep = f['followeeProfile']
            soc = fep['socialFacts']
            boo = (f.wers_followeeStatusOfLoggedInPlayer'] != f.wers_followerStatusOfLoggedInPlayer'])

            if verbose > 0:
                # dump out entire list
                print('{:4d}{}{} {}\t{} {}'.format(count, [' ', '*'][boo]
                                                   , f.wers_followeeStatusOfLoggedInPlayer']
                                                   , f.wers_followerStatusOfLoggedInPlayer']
                                                   , fep['firstName'], fep['lastName']))
            elif boo:
                # disply only those whos soc status match
                print('{:4d} {} {}\t{} {}'.format(count
                                                  , f.wers_followeeStatusOfLoggedInPlayer']
                                                  , f.wers_followerStatusOfLoggedInPlayer']
                                                  , fep['firstName'], fep['lastName']))
                pass
            pass
        start += 200
        pass
    print('processed {} followees'.format(count))
    '''
    pass

def followers():
    count = 0
    wers = [Followers(a) for a in Followers.db_extract(raw=True)()]
    fnfmt = Followers.tab._cfmt['wer_firstName']
    lnfmt = Followers.tab._cfmt['wer_lastName']
    nafmt = fnfmt + ' ' + lnfmt
    fmt0 = '{:4d}{}'
    fmt0+= Followers.tab._cfmt['wers_followeeStatusOfLoggedInPlayer']
    fmt0+= Followers.tab._cfmt['wers_followerStatusOfLoggedInPlayer']
    fmt0+= '\t' + nafmt
    fmt1 = '{:4d} '
    fmt1+= Followers.tab._cfmt['wers_followeeStatusOfLoggedInPlayer']
    fmt1+= Followers.tab._cfmt['wers_followerStatusOfLoggedInPlayer']
    fmt1+= '\t' + nafmt

    for f in wers:
        count += 1
        boo = (f.wers_followeeStatusOfLoggedInPlayer != f.wers_followerStatusOfLoggedInPlayer)

        if vebosity > 0:
            # dump out entire list
            print(fmt0.format(count, [' ', '*'][boo]
                              , f.wers_followeeStatusOfLoggedInPlayer
                              , f.wers_followerStatusOfLoggedInPlayer
                              , f.wer_firstName, f.wer_lastName))
        elif boo:
            # disply only those whos soc status match
            print(fmt1.format(count
                              , f.wers_followeeStatusOfLoggedInPlayer
                              , f.wers_followerStatusOfLoggedInPlayer
                              , f.wer_firstName, f.wer_lastName))
            pass
        pass
    print('processed {} followers'.format(count))
    pass

@cli.command()
def csv():
    '''Generate CVS output, full table.
    (currently only `followers`).'''
    
    wers = [Followers(a) for a in Followers.db_extract(raw=True)()]
    raise SystemExit('Error: not yet finished.  Tomorrow?')

class EnumCache(object):
    def __init__(self, db, name='enum'):
        super().__init__()
        self._db = db
        self._name = name
        self._enumv = {}  # _enum['class']['name'] = val
        self._enums = {}  # _enum['class'][val] = 'name'
        return self._setup()

    def enum_set(self, c, k, v):
        '''map value thru enum cache.'''
        if not c in self._enumv:
            self._enumv[c] = {}
            self._enums[c] = {}
            pass

        if k in self._enumv[c]:
            assert self._enumv[c][k] == v
            assert self._enums[c][v] == k
        else:
            self.execute(f'''INSERT INTO {self._name} VALUES('{c}', '{k}', {v});''')
            self.commit()
            self._enumv[c][k] = v
            self._enums[c][v] = k
            pass
        return v

    def enum_get(self, c, k):
        '''If `c[k]` is not currently in the cache, we add it.'''
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
        '''Establish table in DB if required.  Cache any extant values.'''
        self.gen_tables()
        self.sync_cache()
        pass
    
    def table_exists(self):
        debug(1, f'enum_table_exists({self=}, {self._name=}, {self._db=})')
        return self._db.table_exists(self._name)

    def gen_tables(self, drop=False):
        '''Generate the ENUM table.'''
        debug(1, f'gen_table({self=}, {self._name=}, {self._db=}, {drop=})')

        if drop:
            self.drop_tables()
            pass
        self.execute(f'''CREATE TABLE IF NOT EXISTS {self._name} (cat INT, name TEXT, val INT, UNIQUE(cat, name), PRIMARY KEY(cat, val)) WITHOUT ROWID;''')
        self.commit()
        pass

    def sync_cache(self):
        try:
            res = self.execute(f'''SELECT * FROM {self._name};''')
        except Exception as e:
            print(f'{e=}')
            res = []
            pass
        
        for r in res:
            debug(1, f'{res=}')
            (c, k, v) = r
            if c in self._enumv and k in self._enumv[c]: assert self._enumv[c][k] == v
            else:
                if not c in self._enumv:
                    self._enumv[c] = {}
                    pass
                self._enumv[c][k] = v
                pass
            pass
        return 
    pass

class DataBase(EnumCache):
    cache = {}		# DB universe

    def __init__(self, path=None, reset=False):
        self._path = path = DataBase.db_path(path)
        self._cur  = None

        debug(1, f'init {self=} {self._path=} {DataBase.cache=}')

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
        debug(1, f'del {self=} {self._path=} {DataBase.cache=}')
        if self._path in DataBase.cache:
            del DataBase.cache[self._path]
            pass

    @staticmethod
    def db_path(path=None):
        '''Return the path name.'''
        if path is None:
            zdir = os.getenv('HOME') + '/.zwi/'
            path = zdir + 'zwi.db'
            pass
        return path

    @staticmethod
    def __db_connect(path, reset=False):
        '''Setup DB for access.'''

        if reset and os.path.isfile(path):
            try:
                os.remove(path)
            except Exception as e:
                # print(f'Error: {e}')
                raise e
            pass

        if reset or path not in DataBase.cache:
            try:	# first, try to create the DB
                db = sq.connect(path)
            except Exception as e:
                raise e
            DataBase.cache[path] = db
            pass
        return DataBase.cache[path]

    @classmethod
    def db_connect(cls, path=None, reset=False, drop=False):
        '''Connect to a database.'''
        path = cls.db_path(path)
        if path not in cls.cache:
            return DataBase(path, reset)
        else:
            return cls.cache[path]
        pass
    
    @property
    def db(self):	return self._db
    @property
    def path(self):	return self._path
    @property
    def cursor(self):
        if not self._cur: self._cur = self._db.cursor()
        return self._cur

    def table_exists(self, name):
        '''Query if table exists in DB.'''
        sel = f'''SELECT name FROM sqlite_master WHERE type='table' AND name='{name}';'''
        res = self.execute(sel)
        for tup in res.fetchall():
            if type(tup) is type(()):
                for t in tup:
                    if t == name:
                        debug(1, f'{res=} {tup=} {t=} {t==name=}')
                        return True
                    pass
                pass
            pass
        debug(1, f'{res=} {name in res=}')
        return False

    def execute(self, exe):
        verbo(1, f'{exe}')
        try:
            return self.cursor.execute(exe)
        except Exception as e:
            debug(1, f'{exe}')
            raise Error(f'execute({exe} => {e}')
        pass
        
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

class Table(object):
    '''A class used to manage database columns.'''

    def __init__(self, prefix='', primary=None, copy=None):
        super().__init__()
        if copy is not None:
            self._name = copy._name
            self._nlen = copy._nlen
            self._cfmt = copy._cfmt
            self._meth = copy._meth
            self._prop = copy._prop
            self._type = copy._type
        else:
            self._name = []	# names of columns
            self._nlen = {}	# max length of items in column
            self._cfmt = {}	# column print format
            self._meth = {}	# access method
            self._prop = {}
            self._type = {}
            pass
        self._pref = prefix
        self._primary_key = primary
        return

    def finally__(self, oth):
        '''Manage `inheritance` as best we can.
        It may be the case that the class currently being defined derives from
        a base class with a .tab Table class.
        We need to copy the @col() annotations from the 'base'.
        '''
        if oth is None: return

        debug(1, f'{self=} {oth=} {self._name=} {oth._name=}')
        for c in [ c for c in oth._name if c not in self._name ]:
            self._name.append(c)
            self._meth[c] = oth._meth[c]
            self._type[c] = oth._type[c]
            self._prop[c] = oth._prop[c]
            pass
        return
            
    def col(self, fun):
        '''Add a column definition for the table.
        We also incorporate the @property.'''
        name = fun.__name__
        debug(1, f'col: {self=} {fun=}')
        self._name.append(name)
        self._meth[name] = fun
        self._type[name] = 'TEXT'
        self._prop[name] = property(fun)
        if self._primary_key == name:
            self._type[name] += ' PRIMARY KEY'
            pass
        return self._prop[name]
        
    def change_type(self, name, text):
        '''Change the column type.'''
        self._type[name] = text
        if self._primary_key == name:
            self._type[name] += ' PRIMARY KEY'
            pass
        pass

#    def __repr__(self):
#        return ', '.join(f'{a}' for a in self._name)

    def table_template(self, table_name):
        return ', '.join(f'{a} {b}' for (a, b) in zip(self._name, [self._type[n] for n in self._name]))

    def insert_template(self):
        return ', '.join(f'{a}' for a in self._name)

    def values(self, obj):
        '''Return all the values, matching the columns in the table.
        We need to replace all single ' with double '
        '''
        vals = [str(self._meth[n](obj)).replace("'", "''") for n in self._name]
        return ', '.join(f"'{a}'" for a in vals)

    pass

class Table_v1(Table):
    def __init__(self, prefix='', primary=None, copy=None):
        print(f'{self=} {copy=}')
        super().__init__(prefix=prefix, primary=primary, copy=copy)
        self._enumc = []  # columns using enum mapping
        self._alias = {}  # column name aliasing
        # establish initial alias list based on inderited column names
        for n in self._name:
            self.alias(n)
        return

    def alias(self, fun, alias=None):
        '''Add a column name alias.'''
        if type(fun) is type(''):	# passing in a function name?
            name = fun
        else:
            name = fun.__name__
            pass

        if alias is None:
            # default aliasing is to stop off the prefix
            if '_' in name:
                alias = name.split('_')[1]
            else:
                alias = name
                pass
            pass
        self._alias[name] = alias
        return

    def enumcol(self, fun, alias=None):
        '''This column uses enum mapping.'''
        if type(fun) is type(''):	# passing in a function name?
            name = fun
            rv = None
        else:
            name = fun.__name__
            rv = self.col(fun)
            pass
        self._enumc.append(name)
        self.alias(name, alias)
        debug(2, f'enumcol: {name=} {alias=} {self._enumc=} {rv=}')
        return rv

    def intcol(self, fun):
        '''This column uses integer mapping.'''
        print(f'intcol: {self=} {fun=}')
        self.change_type(fun, 'INT')
        return

    def table_template(self, table_name):
        '''Generate table with ENUM rows as needed.'''
        typ = self._type.copy()
        print(f'{self=} {typ=}')
        for k in self._enumc:
            # Gave up trying to make REFERENCES work.
            typ[k] = 'INT'
            pass
        return ', '.join(f'{a} {b}' for (a, b) in zip(self._name, [typ[k] for k in self._name]))

    def insert_template(self):
        return ', '.join(f'{a}' for a in self._name)

    def values(self, obj, table_name, db):
        '''Manage value/enum mappings.'''
        vals = []
        debug(3, f'values: {self._name=}')
        for col in self._name:
            # if n in ['addDate', 'delDate']: continue
            val = str(self._meth[col](obj)).replace("'", "''")
            if col in self._enumc:
                # this value uses enum mapping: make sure we have one defined
                col_enum = db.enum_get(0, col)
                val = db.enum_get(col_enum, val)
                pass

            vals.append(val)
            pass
        debug(3, f'vals: {vals}')
        # Here we single quote the values.
        # We are relying on SQLite3 to coerce the values approriately.
        # XXX: am I sure I handle 'hi''there''''' correctly?
        #
        # If I wish to use enum mapping for the date/time cols, I need to gen the
        # time val myself.
        # return ', '.join(f"'{a}'" for a in vals) + ''', datetime('now', 'localtime'), 'not yet' '''
        # 
        return ', '.join(f"'{a}'" for a in vals)
    pass

class Followers(object):

    tab = Table(primary='followerId')
    template = {
        'id': 0,
        'followerId': 0,
        'followeeId': 0,
        'status': '',
        'isFolloweeFavoriteOfFollower': False,
        'followerProfile': {
            'id': 0,
            'publicId': '',
            'firstName': 'Joe',
            'lastName': 'Blogs',
            'male': True,
            'imageSrc': '',
            'imageSrcLarge': '',
            'playerType': '',
            'countryAlpha3': '',
            'countryCode': 0,
            'useMetric': True,
            'riding': False,
            'privacy': {
                'approvalRequired': False,
                'displayWeight': False,
                'minor': False,
                'privateMessaging': False,
                'defaultFitnessDataPrivacy': False,
                'suppressFollowerNotification': False,
                'displayAge': True,
                'defaultActivityPrivacy': '',
            },
            'socialFacts': {
                'profileId': 0,
                'followersCount': 0,
                'followeesCount': 0,
                'followeesInCommonWithLoggedInPlayer': 0,
                'followerStatusOfLoggedInPlayer': '',
                'followeeStatusOfLoggedInPlayer': '',
                'isFavoriteOfLoggedInPlayer': True
            },
            'worldId': None,
            'enrolledZwiftAcademy': False,
            'playerTypeId': 1,
            'playerSubTypeId': None,
            'currentActivityId': None,
            'likelyInGame': False
        },
        'followeeProfile': None,
    }

    @tab.col
    def followerId(self):        return self._data['followerId']
    @tab.col
    def followeeId(self):        return self._data['followeeId']
    @tab.col
    def status(self):            return self._data['status']
    @tab.col
    def isFolloweeFavoriteOfFollower(self):
        return self._data['isFolloweeFavoriteOfFollower']

    @property
    def followerProfile(self):	return self._data['followerProfile']
    @tab.col
    def wer_publicId(self):	return self._wer['publicId']
    @tab.col
    def wer_firstName(self):	return self._wer['firstName']
    @tab.col
    def wer_lastName(self):	return self._wer['lastName']
    @tab.col
    def wer_male(self):	return self._wer['male']
    @tab.col
    def wer_imageSrc(self):	return self._wer['imageSrc']
    @tab.col
    def wer_imageSrcLarge(self):	return self._wer['imageSrcLarge']
    @tab.col
    def wer_playerType(self):	return self._wer['playerType']
    @tab.col
    def wer_countryAlpha3(self):	return self._wer['countryAlpha3']
    @tab.col
    def wer_countryCode(self):	return self._wer['countryCode']
    @tab.col
    def wer_useMetric(self):	return self._wer['useMetric']
    @tab.col
    def wer_riding(self):	return self._wer['riding']

    @property
    def wer_privacy(self):	return self._wer['privacy']

    @tab.col
    def werp_displayWeight(self):	return self._werp['displayWeight']
    @tab.col
    def werp_minor(self):		return self._werp['minor']
    @tab.col
    def werp_privateMessaging(self):	return self._werp['privateMessaging']
    @tab.col
    def werp_defaultFitnessDataPrivacy(self):		return self._werp['defaultFitnessDataPrivacy']
    @tab.col
    def werp_suppressFollowerNotification(self):	return self._werp['suppressFollowerNotification']
    @tab.col
    def werp_displayAge(self):				return self._werp['displayAge']
    @tab.col
    def werp_defaultActivityPrivacy(self):		return self._werp['defaultActivityPrivacy']

    @property
    def wer_socialFacts(self):		return self._wer['socialFacts']

    @tab.col
    def wers_followersCount(self):	return self._wers['followersCount']
    @tab.col
    def wers_followeesCount(self):	return self._wers['followeesCount']
    @tab.col
    def wers_followeesInCommonWithLoggedInPlayer(self):	return self._wers['followeesInCommonWithLoggedInPlayer']
    @tab.col
    def wers_followerStatusOfLoggedInPlayer(self):	return self._wers['followerStatusOfLoggedInPlayer']
    @tab.col
    def wers_followeeStatusOfLoggedInPlayer(self):	return self._wers['followeeStatusOfLoggedInPlayer']
    @tab.col
    def wers_isFavoriteOfLoggedInPlayer(self):		return self._wers['isFavoriteOfLoggedInPlayer']

    @tab.col
    def wer_worldId(self):			return self._wer['worldId']
    @tab.col
    def wer_enrolledZwiftAcademy(self):		return self._wer['enrolledZwiftAcademy']
    @tab.col
    def wer_playerTypeId(self):			return self._wer['playerTypeId']
    @tab.col
    def wer_playerSubTypeId(self):		return self._wer['playerSubTypeId']
    @tab.col
    def wer_currentActivityId(self):		return self._wer['currentActivityId']
    @tab.col
    def wer_likelyInGame(self):			return self._wer['likelyInGame']

    @property
    def followeeProfile(self):			return self._data['followeeProfile']

    @tab.col
    def addDate(self):				return self._addDate
    @tab.col
    def delDate(self):				return self._delDate
    
    @classmethod
    def convert(cls, obj):
        '''Convert db-format object to 'native'.'''
        col = cls.tab._name # + ['addDate', 'delDate']

        if type(obj) is not type([]) and type(obj) is not type(()):
            print( type(obj), type([]), type(obj), type(()))
            raise SystemExit('funny type for conversion {!r}.'.format(type(obj)))

        if len(obj) != len(col):
            raise SystemExit(f'{len(obj)=} != {len(col)=}.')

        # I should have flattened the on-wire format to the db-format and
        # made that the basic layout.  Oh well.
        wer  = [c[4:]  for c in col if c.startswith('wer_')]
        werp = [c[5:]  for c in col if c.startswith('werp_')]
        wers = [c[5:]  for c in col if c.startswith('wers_')]
        rema = [c for c in col if not '_' in c and not c.startswith('wer')]

        werx  = [obj[col.index('wer_'+c)]  for c in wer]
        werpx = [obj[col.index('werp_'+c)] for c in werp]
        wersx = [obj[col.index('wers_'+c)] for c in wers]
        remax = [obj[col.index(c)] for c in rema]

        wer  = dict(zip(wer , werx))
        werp = dict(zip(werp, werpx))
        wers = dict(zip(wers, wersx))
        top  = dict(zip(rema, remax))

        top['followerProfile'] = wer
        top['followeeProfile'] = None
        top['followerProfile']['privacy'] = werp
        top['followerProfile']['socialFacts'] = wers

        return top

#    def __repr__(self):
#        return str(self._data)

    def __init__(self, w=None):
        super().__init__()
        self._addDate = datetime.now().isoformat(timespec='minutes')
        self._delDate = 'later'

        # The initialiser is either None, a type({}) or a type(()) (or type([]))
        #
        # type({}): wire format
        # type(()): db-format
        #
        if w is None: w = Followers.template

        if type(w) is not type({}):
            # need to convert the db-format to wire-format
            w =  self.__class__.convert(w)
            pass

        self._data = w
        self._wer  = w['followerProfile']
        self._wee  = w['followeeProfile']

        if self._wer:
            self._werp = w['followerProfile']['privacy']
            self._wers = w['followerProfile']['socialFacts']
            pass

        if self._wee:
            self._weep = w['followeeProfile']['privacy']
            self._wees = w['followeeProfile']['socialFacts']
            pass
        pass

    @classmethod
    @property
    def table_name(cls):	return cls.__name__.lower()

    @classmethod
    def table_template(cls):
        # cls.tab.change_type('followerId', 'text PRIMARY KEY')
        verbo(1, f"CREATE TABLE IF NOT EXISTS {cls.table_name}({cls.tab.table_template(cls.table_name)})")
        return f"CREATE TABLE IF NOT EXISTS {cls.table_name}({cls.tab.table_template(cls.table_name)});"

    @classmethod
    def insert_template(cls, obj, xtra_col='', xtra_val=''):
        return f'''INSERT INTO {cls.table_name}({cls.tab.insert_template()} {xtra_col})
        VALUES({cls.tab.values(obj)} {xtra_val});'''

    @classmethod
    def gen_table(cls, db, drop=False):
        '''Generate the sqlite3 table for this class.'''
        debug(1, f'gen_table({cls=}, {db=}, {drop=})')
        if drop: db.execute(f'''DROP TABLE IF EXISTS {cls.table_name};''')
        t = cls.table_template()
        r = db.execute(t)
        debug(1, f'{r.fetchall()=}')
        db.commit()
        return r

    def db_insert(self, db, commit=False):
        '''Write the current object to the db table.
        Insert into table columns(...) values(...)'''
        t = self.__class__.insert_template(self, db)
        r = db.execute(t)
        if commit: db.commit()
        return r

    @classmethod
    def db_colmax(cls, db):
        '''Determine the max lengths of the columns.'''

        for c in cls.tab._name:
            cls.tab._nlen[c] = len(c)
            pass

        for c in cls.tab._name:
            try:
                res = db.execute(f'''SELECT {c}, length({c}) FROM {cls.table_name} ORDER BY length({c}) DESC;''')
            except Exception as e:
                # no entries in the DB
                print(f'{type(e)} Error: {e}')
                # print(f'Error: {e}')
                error('You may have to run the `reset` command.')
                pass

            r = res.fetchone()	# is there a way to just return one result in above?
            if r is not None:
                # print(f'{c=}:{r=}')
                lr = len(str(r[0]))
                if lr > cls.tab._nlen[c]:
                    cls.tab._nlen[c] = lr
                    pass
                pass
            pass

        for c in cls.tab._name:
            lr = cls.tab._nlen[c]
            if c != 'wer_lastName':
                cls.tab._cfmt[c] = '{:>%d.%d}' % (lr, lr)
            else:
                cls.tab._cfmt[c] = '{:<%d.%d}' % (lr, lr)
            pass
        
        pass

    @classmethod
    def _db_extract(cls, db, cols, arraysize=200):
        '''Extract entries from the database.'''

        sel = ', '.join(f'{a}' for a in cols)
        r = db.execute(f'''SELECT {sel} FROM {cls.table_name} ORDER BY rowid''')

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


    @classmethod
    def db_extract(cls, db=None, cols=None, arraysize=200, raw=False):
        '''Extract entries from the database.'''
        if cols is None:
            cols = cls.tab._name
        else: # verify the colums
            for c in cols:
                if not c in cls.tab._name:
                    raise Exception(f'{c}: funny column name')
                pass
            pass

        if db is None:
            # XXX: this is a mess.
            db = db_setup()
            pass

        if len(cls.tab._nlen) == 0:
            print('Error: table not setup with column lengths.')
            sys.exit(1)
            pass


        # generate the format string
        #fmt = ' '.join(['{:>%d.%ds}' % (l, l) for l in [cls.tab._nlen[c] for c in cols]])
        fmt = ' '.join(f for f in [cls.tab._cfmt[c] for c in cols])
        hdr = fmt.format(*cols)
        sel = ', '.join(f'{a}' for a in cols)

        try:
            r = db.execute(f'''SELECT {sel} FROM {cls.table_name} ORDER BY rowid''')
        except Exception as e:
            print('Warning:', e)
            print(f'Warning: cannot SELECT from table `{cls.table_name}`')
            pass

        if raw:
            # provide a raw generator
            # XXX: fix this so that the cooked gen uses the raw gen
            def rgen():
                # xxx: DO NOT: yield cols for raw
                while True:
                    ar = r.fetchmany(arraysize)

                    if not ar:
                        break
                    for e in ar:
                        yield e
                pass
            return rgen

        def gen():
            import unicodedata

            yield hdr
            while True:
                ar = r.fetchmany(arraysize)

                if not ar:
                    break
                for e in ar:
                    # having problems with embedded unicode chars
                    for i in range(len(e)):
                        if type(e[i]) is type('') and not e[i].isascii():
                            # at least one member is not ASCII
                            if type(e) is not type([]):
                                # convert to array so we can modify
                                e = [*e]
                                pass
                            e[i] = unicodedata.normalize('NFKD', e[i]).encode('ascii', 'ignore').decode()
                            pass
                        pass
                    yield fmt.format(*e)
                    pass
                pass
            pass

        # return the generator
        return gen
    pass

class Followers_v1(Followers):
    '''Version 1 of the `followers` table.

    Main differences are:
    	* use of ENUMs for certain column data in DB
    '''

    tab = Table_v1(primary='followerId', copy=Followers.tab)

    def __init__(self, w=None):
        if isinstance(w, Followers):
            print(f'init from {w=} {type(w)=}')
            w = w._data
            pass
        super().__init__(w=w)
        pass

    @classmethod
    def insert_template(cls, obj, db):
        return f'''INSERT INTO {cls.table_name}({cls.tab.insert_template()})
        VALUES({cls.tab.values(obj, cls.table_name, db)});'''

    @classmethod
    def gen_table(cls, db, drop=False):
        '''Generate the sqlite3 table for this class.'''
        # cls.gen_enum_table(db, drop)
        return super().gen_table(db, drop)

    def values(self, db):
        print(f'values - {self=}, {db=} {self.tab=}')
        return self.tab.values(self, self.table_name, db)
    
    @classmethod
    def db_extract(cls, db=None, cols=None, arraysize=200, raw=False):
        '''Extract entries from the database.'''

        assert db is not None
        if cols is None: cols = cls.tab._name

        # generate the format string
        fmt = ' '.join(f for f in [cls.tab._cfmt[c] for c in cols])
        hdr = fmt.format(*[cls.tab._alias[c] for c in cols])
        print(f'{[cls.tab._alias[c] for c in cols]}')

        g = cls._db_extract(db, cols, arraysize)

        def gen():
            import unicodedata

            if not raw: yield hdr

            for e in g():
                # map back thru enum cache
                for i in range(len(e)):
                    c = cols[i]
                    if c in cls.tab._enumc:
                        if type(e) is not type([]): e = [*e]
                        e[i] = db.enum_str(db.enum_get(0, c), e[i])
                        pass
                    if not raw and type(e[i]) is type('') and not e[i].isascii():
                        if type(e) is not type([]): e = [*e]
                        e[i] = unicodedata.normalize('NFKD', e[i]).encode('ascii', 'ignore').decode()
                        pass
                    pass
                if raw: yield e
                else:
                    try:
                        yield fmt.format(*[str(x) for x in e])
                    except Exception as ex:
                        print(f'{ex}')
                        print(f'{fmt=}')
                        print(f'{e}')
                        error('')
                        pass
                    pass
                pass
            pass

        # return the generator
        return gen

    # these entries are to be treated as enums
    tab.enumcol('status')
    tab.enumcol('isFolloweeFavoriteOfFollower', 'favorite')
    tab.enumcol('wer_male')
    tab.enumcol('wer_firstName')
    tab.enumcol('wer_lastName')
    tab.enumcol('wer_playerType')
    tab.enumcol('wer_countryAlpha3')
    tab.enumcol('wer_useMetric')
    tab.enumcol('wer_riding')
    tab.enumcol('werp_displayWeight')
    tab.enumcol('werp_minor')
    tab.enumcol('werp_privateMessaging')
    tab.enumcol('werp_defaultFitnessDataPrivacy')
    tab.enumcol('werp_suppressFollowerNotification')
    tab.enumcol('werp_displayAge')
    tab.enumcol('werp_defaultActivityPrivacy')
    tab.enumcol('wers_followerStatusOfLoggedInPlayer')
    tab.enumcol('wers_followeeStatusOfLoggedInPlayer')
    tab.enumcol('wers_isFavoriteOfLoggedInPlayer')
    tab.enumcol('wer_worldId')
    tab.enumcol('wer_enrolledZwiftAcademy')
    tab.enumcol('wer_playerTypeId')
    tab.enumcol('wer_playerSubTypeId')
    tab.enumcol('wer_currentActivityId')
    tab.enumcol('wer_likelyInGame')
    tab.enumcol('addDate')
    tab.enumcol('delDate')

    # these are ints
    tab.intcol('followerId')
    tab.intcol('followeeId')
    tab.intcol('wer_countryCode')
    tab.intcol('wers_followersCount')
    tab.intcol('wers_followeesCount')
    tab.intcol('wers_followeesInCommonWithLoggedInPlayer')
    
    # This needs to come last:
    __final = tab.finally__(Followers.tab)
    pass

@cli.command()
def test():
    '''Perform some modicum of internal tests.'''

    try:
        raise Exception('yo!')
    except Exception as e:
        print(f'{e!r}: oops!')
        pass
    
    db0 = DataBase.db_connect()
    db1 = DataBase.db_connect('/tmp/zwi_test.db', reset=True)
    db2 = DataBase.db_connect('/tmp/zwi_test.db', reset=True)
    db3 = DataBase.db_connect()
    print(f'{db0==db3=} {db2!=db3=}')
    
    print(f"{db1=} {db1.table_exists('followers')=}")
    print(f"{db1=} {db1.table_exists('followees')=}")
    
    Followers.gen_table(db1, drop=False)
    Followers.gen_table(db1, drop=False)

    print(f"{db1=} {db1.table_exists('followers')=}")
    print(f"{db1=} {db1.table_exists('followees')=}")

    print(f"{db1=} {db1.table_exists('followers_v1')=}")
    print(f"{db1=} {db1.table_exists('followees_v1')=}")

    Followers_v1.gen_table(db1, drop=True)
    Followers_v1.gen_table(db1, drop=False)

    print(f"{db1=} {db1.table_exists('followers_v1')=}")
    print(f"{db1=} {db1.table_exists('followees_v1')=}")

    fo = Followers_v1()
    print(f'''{fo.values(db1)=}''')
    
    # slurp in the followers from the DB and reconstitute.
    wers = [a for a in Followers.db_extract(raw=True)()]
    wers_v1 = []
    # write out as a _v1 type table
    count = 0
    for w in wers:
        count += 1
        if count <= 10:
            print(f'{[w[i] for i in range(8)]}')
            pass
        v1 = Followers_v1(w)
        v1.db_insert(db1)
        wers_v1.append(v1)
        got = False
        try:
            v1.db_insert(db1)
            v1.db_insert(db1)
            v1.db_insert(db1)
        except Exception as e:
            debug(3, f'expected exception: {e!r}')
            got = True
            pass

        if not got:
            db1.commit()
            raise SystemExit('no exception on multiple inserts.')

        if count >= 100: break
            
        # v1.db_update(db1, v1)
        pass
   
    db1.commit()
    Followers_v1.db_colmax(db1)

    wers = [a for a in Followers_v1.db_extract(db1, raw=True)()]
    count = 0
    if len(wers) >= 1:
        playerId = wers[0][1]
        for w in wers:
            count += 1
            if count <= 10:
                # just display the first 10
                print(f'{[w[i] for i in range(8)]}')
                pass
            if w[1] != playerId:
                # sanity check: all these have playerId there
                print(f'{w[1]=} != {playerId} -- {[w[i] for i in range(8)]}')
                pass
            if w[2] != 'IS_FOLLOWING':
                # sanity check: all these are following
                print(f'''{w[2]=} != 'IS_FOLLOWING' -- {[w[i] for i in range(8)]}''')
                pass
            pass
        pass

    setup(1,1)
    _gui(db1)
    db1.close()

    pass

def db_setup(reset=False):
    '''Generate the initial database.
    Currently, I only snarf in the followers table.
    Currently, I do not handle updates.'''

    db = DataBase.db_connect(reset=reset)

    nascent = not db.table_exists('followers')
    if nascent:
        Followers.gen_table(dbo)

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
    '''Reset the database, and re-fetch information from Zwift.'''
    db_setup(reset=True)
    return 0

@cli.command()
def gui():
    '''Pop up a GUI window, displaying results from the DB.'''

    return _gui(db=None)

def _gui(db=None):
    import sqlite3 as sq
    import tkinter as tk
    from tkinter.constants import RIGHT, BOTH, LEFT, END
    from tkinter.scrolledtext import ScrolledText
    from tkinter.font import Font

    class GuiApp(tk.Frame):
        def __init__(self, db, master=None):
            self._buttons = {}
            self._fonts = {}
            self._db = db
            super().__init__(master)
            self.master = master
            self.pack()
            self.create_widgets()
            self.refresh()
            pass

        def create_widgets(self):
            self._fonts['courier'] = Font(family='Courier', size=16)
            self._buttons['quit'] = tk.Button(self, text='quit', fg='red', command=self.master.destroy)
            self._buttons['quit'].pack(side='top')
            self._buttons['refresh'] = tk.Button(self, text='refresh', command=self.refresh)
            self._buttons['refresh'].pack(side='top')

            self._box = ScrolledText(bg='black', fg='green', height=32, width=128, font=self._fonts['courier'])
            self._box.insert(END, 'hit refresh')
            self._box.configure(state='disabled')
            self._box.pack(fill=BOTH, side=LEFT, expand=True)
            self._box.focus_set()
            pass

        def refresh(self):
            b = self._box
            
            rows = Followers_v1.db_extract(self._db, ['followerId', 'wer_firstName', 'wer_lastName', 'wer_playerType', 'isFolloweeFavoriteOfFollower'])

            b.configure(state='normal')
            b.delete('1.0', END)

            for r in rows():
                b.insert(END, r + '\n')
                pass

            b.configure(state='disabled')
            b.pack(fill=BOTH, side=LEFT, expand=True)
            b.focus_set()
            pass

        def quit(self):
            sys.exit(0)
            pass
        pass

    if not db: db = DataBase.db_connect()

    gui = GuiApp(db, master=tk.Tk())
    gui.mainloop()
    pass
  
if __name__ == '__main__':
    try:
        cli()
        sys.exit(0)
    except Exception as e:
        debug(1, f'{type(e)=}\n{e!r}')
        print(f'{e}')
        if debug_lvl > 0:
            raise Exception('oops!') from e
        sys.exit(1)

