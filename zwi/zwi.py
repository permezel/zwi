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

@click.group()
def cli():
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
        print('Cannot set zwi.py username')
        sys.exit(2)
        pass

    try:
        keyring.set_password('zwi.py', name, password)
    except keyring.errors.PasswordSetError:
        print('Cannot set zwi.py username+password')
        sys.exit(3)
        pass

    try:
        if keyring.get_password('zwi.py', 'username') != name:
            print('keyring username mismatch')
            sys.exit(2)
            pass
    
        if keyring.get_password('zwi.py', name) != password:
            print('keyring password mismatch')
            sys.exit(3)
            pass

        sys.exit(0)
    except keyring.errors.KeyringError as e:
        print('***keyring error:', e)
        sys.exit(4)
        pass
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
        pass
    except keyring.errors.KeyringError as e:
        print('***keyring error:', e)
        sys.exit(5)
        pass

    try:
        keyring.delete_password('zwi.py', name)
    except keyring.errors.KeyringError as e:
        print('Trying to delete password: ***keyring error:', e)
        pass
        
    try:
        keyring.delete_password('zwi.py', 'username')
    except keyring.errors.KeyringError as e:
        print('Trying to delete username: ***keyring error:', e)
        pass

    sys.exit(0)
    pass
        
    
@cli.command()
@click.option('-v', '--verbose', count=True)
def wees(verbose):
    """Display followees who are not following me."""
    followees(verbose)
    sys.exit(0)
    pass

@cli.command()
@click.option('-v', '--verbose', count=True)
def wers(verbose):
    """Display followers who I am not following."""
    followers(verbose)
    sys.exit(0)
    pass
    
def zwi_init():
    """Initialise communications with Zwift API."""

    try:
        name = keyring.get_password('zwi.py', 'username')
    except Exception as e:
        print('Error:', e)
        print('Cannot locate `username` entry -- re-run `auth`.')
        sys.exit(1)
        pass

    if name is None:
        print('Error: no `username` has been specified -- re-run `auth`.')
        sys.exit(1)
        pass

    try:
        password = keyring.get_password('zwi.py', name)
    except Exception as e:
        print('Error:', e)
        print('Cannot locate `password` entry for user {} -- re-run `auth`.'.format(name))
        sys.exit(1)
        pass

    try:
        cl = Client(name, password)
        pr = cl.get_profile()
        pr.check_player_id()
        print('player_id:', pr.player_id)
        return (cl, pr)
    except Exception as e:
        print('Error:', e)
        print('Authentication failure for user {}.'.format(name))
        sys.exit(1)
        pass
    pass


def followees(verbose):
    count = 0
    """
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
    """
    pass

def followers(verbose):
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

        if verbose > 0:
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
@click.option('-v', '--verbose', count=True)
def csv(verbose):
    """Generate CVS output, full table.
    (currently only `followers`)."""
    wers = [Followers(a) for a in Followers.db_extract(raw=True)()]
    print('Error: not yet finished.  Tomorrow?')
    sys.exit(1)
    pass

class Table:
    def __init__(self, prefix='', primary=None):
        self._name = []	# names of columns
        self._nlen = {}	# max length of items in column
        self._cfmt = {}	# column print format
        self._meth = {}	# access method
        self._prop = {}
        self._type = {}
        self._pref = prefix
        self._primary_key = primary
        pass

    def col(self, fun):
        """Add a column definition for the table.
        We also incorporate the @property."""
        name = fun.__name__
        self._name.append(name)
        self._meth[name] = fun
        self._type[name] = 'text'
        self._prop[name] = property(fun)
        if self._primary_key == name:
            self._type[name] += ' PRIMARY KEY'
            pass
        return self._prop[name]
        
    def change_type(self, name, text):
        """Change the column type."""
        self._type[name] = text
        pass

    def __repr__(self):
        return ', '.join(f'{a}' for a in self._name)

    def table_template(self):
        return ', '.join(f'{a} {b}' for (a, b) in zip(self._name, [self._type[n] for n in self._name]))

    def insert_template(self):
        return ', '.join(f'{a}' for a in self._name)

    def values(self, obj):
        """Return all the values, matching the columns in the table.
        We need to replace all single ' with double '
        """
        vals = [str(self._meth[n](obj)).replace("'", "''") for n in self._name]
        # print('vals:', vals)
        return ', '.join(f"'{a}'" for a in vals)

    pass

class DataBase(object):
    cache = {}		# DB universe

    def __init__(self, path=None, reset=False):
        self._path = None
        super().__init__()
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

        DataBase.cache[path] = self
        pass

    def __del__(self):
        debug(1, f'del {self=} {self._path=} {DataBase.cache=}')
        if self._path in DataBase.cache:
            del DataBase.cache[self._path]
            pass

    @staticmethod
    def db_path(path=None):
        """Return the path name."""
        if path is None:
            zdir = os.getenv('HOME') + '/.zwi/'
            path = zdir + 'zwi.db'
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
            try:	# first, try to create the DB
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
    def db(self):	return self._db
    @property
    def path(self):	return self._path
    @property
    def cursor(self):
        if not self._cur: self._cur = self._db.cursor()
        return self._cur

    def table_exists(self, name):
        """Query if table exists in DB."""
        cur = self.cursor
        sel = f'''SELECT name FROM sqlite_master WHERE type='table' AND name='{name}';'''
        try:
            res = cur.execute(sel)
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
        except Exception as e:
            print(sel)
            raise Error(e)
        pass
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
        """Convert db-format object to 'native'."""
        col = cls.tab._name # + ['addDate', 'delDate']

        if type(obj) is not type([]) and type(obj) is not type(()):
            print( type(obj), type([]), type(obj), type(()))
            print('Error: funny type for conversion {!r}.'.format(type(obj)))
            sys.exit(1)
            pass
        if len(obj) != len(col):
            print('Error: obj len {} != #cols {}.'.format(len(obj), len(col)))
            sys.exit(1)
            pass
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

    def __repr__(self):
        return str(self._data)

    def __init__(self, w=None):
        super().__init__()
        self._addDate = ''
        self._delDate = ''

        # The initialiser is either None, a type({}) or a type(()) (or type([]))
        #
        # type({}): wire format
        # type(()): db-format
        #
        if w is None: w = Followers.template

        if type(w) is not type({}):
            # need to convert the db-format to wire-format
            w =  Followers.convert(w)
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
    def table_template(cls):
        cls.tab.change_type('followerId', 'text PRIMARY KEY')
        return "CREATE TABLE IF NOT EXISTS followers(" + cls.tab.table_template() + ")"

    @classmethod
    def insert_template(cls, obj, xtra_col='', xtra_val=''):
        ins = "INSERT INTO followers(" + cls.tab.insert_template() + xtra_col + ")\n"
        ins += "VALUES(" + cls.tab.values(obj) + xtra_val + ")"
        return ins

    @classmethod
    def gen_table(cls, db):
        """Generate the sqlite3 table for this class."""
        verbo(1, f'gen_table({cls=}, {db=})')
        cur = db.cursor()
        try:
            t = cls.table_template()
            r = cur.execute(t)
            verbo(1, f'{r.fetchall()=}')
            db.commit()
            return r
        except db.Error as e:
            print(f'Error: {e}')
            sys.exit(1)

    def db_insert(self, db, commit=False):
        """Write the current object to the db table.
        Insert into table columns(...) values(...)"""
        cur = db.cursor()
        cls = self.__class__
        t = cls.insert_template(self)
        try:
           r = cur.execute(t)
           if commit: db.commit()
           return r
        except db.Error as e:
           print(t)
           print(f'Error: {e}')
           sys.exit(1)

    @classmethod
    def db_colmax(cls, db):
        """Determine the max lengths of the columns."""

        for c in cls.tab._name:
            cls.tab._nlen[c] = len(c)
            pass

        for c in cls.tab._name:
            cur = db.cursor()	# do I need a new cursor each time?
            try:
                res = cur.execute('SELECT ' +c+', length(' +c+ ') FROM followers ORDER BY length(' +c+ ') DESC')
            except Exception as e:
                # no entries in the DB
                print(f'Error: {e}')
                print('You may have to run the `reset` command.')
                sys.exit(1)

            r = res.fetchone()	# is there a way to just return one result in above?
            if r is not None:
                lr = len(r[0])
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
    def db_extract(cls, db=None, cols=None, arraysize=200, raw=False):
        """Extract entries from the database."""
        if cols is None:
            cols = cls.tab._name
        else: # verify the colums
            for c in cols:
                if not c in cls.tab._name:
                    raise Exception('{}: funny column name'.format(c))
                pass
            pass

        if db is None:
            # XXX: this is a mess.
            db = db_setup()
            pass

        if len(cls.tab._nlen) == 0:
            print('Error: table no setup with column lengths.')
            sys.exit(1)
            pass

        # generate the format string
        #fmt = ' '.join(['{:>%d.%ds}' % (l, l) for l in [cls.tab._nlen[c] for c in cols]])
        fmt = ' '.join(f for f in [cls.tab._cfmt[c] for c in cols])
        hdr = fmt.format(*cols)
        cur = db.cursor()
        sel = ', '.join(f'{a}' for a in cols)

        try:
            r = cur.execute('SELECT ' +sel+ ' FROM followers ORDER BY rowid')
        except Exception as e:
            print('Warning:', e)
            print('Warning: cannot SELECT from table `followers`')
            pass

        if raw:
            # provide a raw generator
            # XXX: fix this so that the cooked gen uses the raw gen
            def rgen():
                # xxx: DO NOT: yield cols for raw
                while True:
                    ar = cur.fetchmany(arraysize)

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
                ar = cur.fetchmany(arraysize)

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

@cli.command()
@click.option('-v', '--verbose', count=True)
def test(verbose):
    """Perform some modicum of internal tests."""
    global verbosity
    verbosity = verbose

    db0 = DataBase.db_connect()
    db1 = DataBase.db_connect('/tmp/zwi_test.db', reset=True)
    db2 = DataBase.db_connect('/tmp/zwi_test.db', reset=True)
    db3 = DataBase.db_connect()
    print(f'{db0==db3=} {db2!=db3=}')
    
    print(f"{db1=} {db1.table_exists('followers')=}")
    print(f"{db1=} {db1.table_exists('followees')=}")
    
    Followers.gen_table(db1.db)
    Followers.gen_table(db1.db)

    print(f"{db1=} {db1.table_exists('followers')=}")
    print(f"{db1=} {db1.table_exists('followees')=}")

    # slurp in the followers from the DB and reconstitute.
    wers = [a for a in Followers.db_extract(raw=True)()]

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
                print(f'{w[2]=} != {playerId} -- {[w[i] for i in range(8)]}')
                pass
            pass
        pass
    pass

def db_setup(reset=False):
    """Generate the initial database.
    Currently, I only snarf in the followers table.
    Currently, I do not handle updates."""

    dbo = DataBase.db_connect(reset=reset)
    db = dbo.db

    nascent = not dbo.table_exists('followers')
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
    """Reset the database, and re-fetch information from Zwift."""
    db_setup(reset=True)
    return 0

@cli.command()
@click.option('-v', '--verbose', count=True)
def gui(verbose):
    """Pop up a GUI window, displaying results from the DB."""

    import sqlite3 as sq
    import tkinter as tk
    from tkinter.constants import RIGHT, BOTH, LEFT, END
    from tkinter.scrolledtext import ScrolledText
    from tkinter.font import Font

    class GuiApp(tk.Frame):
        def __init__(self, master=None):
            self._buttons = {}
            self._fonts = {}
            try:
                self._db = db_setup()
            except sq.Error as e:
                print(e)
                return

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
            
            rows = Followers.db_extract(self._db, ['followerId', 'wer_firstName', 'wer_lastName', 'wer_playerType', 'isFolloweeFavoriteOfFollower'])

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

    gui = GuiApp(master=tk.Tk())
    gui.mainloop()
    pass
  
if __name__ == '__main__':
    try:
        cli()
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)
        pass
    pass



