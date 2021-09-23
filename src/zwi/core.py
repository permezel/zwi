# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.
#
# Move the Zwi common stuff into a package
#
"""Zwi core stuff."""
import os
import urllib3
import sqlite3 as sq
from datetime import datetime
from dataclasses import dataclass, fields
from .util import Error, debug, verbo, verbo_p

try:
    import zwift
    from zwift import Client
    import keyring
except Exception as __ex:
    print('import error', __ex)
    raise SystemExit('please run: pip3 install zwift-client keyring')

# Cache of authentication, so we establish at most once
_zwi_auth_cache = {}


def get_zdir(subdir: str = None, mkdir: bool = True) -> str:
    """Establish local Zwi directory."""

    if subdir is not None:
        zdir = get_zdir() + subdir + os.sep
    else:
        zdir = os.getenv('HOME') + os.sep + '.zwi' + os.sep
        pass

    if mkdir and not os.path.isdir(zdir):
        try:
            os.mkdir(zdir)
        except Exception as e:
            print(f'Cannot create zwi directory: {zdir}')
            print(f'{e}')
            raise SystemExit(f'Cannot create {zdir}')
        pass
    return zdir


def get_zpath(dname: str = None, fname: str = None, subdir: str = None,
              mkdir: bool = True) -> str:
    """Provide the default database path, or overrides to it."""
    dname = get_zdir(subdir=subdir, mkdir=mkdir) if dname is None else dname
    fname = 'zwi.db' if fname is None else fname
    if dname[-1] == os.sep:
        return dname + fname
    else:
        return dname + os.sep + fname


def auth_user(key='zwi.py'):
    """Return the user ID saved."""
    try:
        name = keyring.get_password(key, 'username')
    except Exception as e:
        print('Error:', e)
        raise SystemExit(
            f'{e!r}: Cannot locate `username` entry -- re-run `auth`.')

    return name


def auth_passwd(name, key='zwi.py'):
    """Return the password."""
    try:
        passwd = keyring.get_password(key, name)
    except Exception as e:
        print('Error:', e)
        raise SystemExit(f'{e!r} Cannot locate `password` entry for user'
                         + f' {name} -- re-run `auth`.')

    return passwd


def auth(name, password, key='zwi.py'):
    """Establish the authentication."""
    try:
        cl = Client(name, password)
        # there is no error checking in the above
        # but if I force a fetch as below, I can discover
        # if there are issues.
        token_data = cl.auth_token.fetch_token_data()
        if 'access_token' not in token_data:
            estr = 'error'
            for k in ['error', 'error_description']:
                if k in token_data:
                    debug(1, f'{k:22} {token_data[k]}')
                    estr += f': {token_data[k]}'
                pass
            raise SystemExit(estr)
        else:
            pr = cl.get_profile()
            pr.check_player_id()
    except urllib3.exceptions.HTTPError as e:
        raise SystemExit(f'Cannot connect to Zwift: {e}')
    except ConnectionError as e:
        raise SystemExit(f'Cannot connect to Zwift: {e}')
    except Exception as e:
        raise SystemExit(f'Authentication failure: {e}')

    try:
        keyring.set_password(key, 'username', name)
    except keyring.errors.PasswordSetError:
        raise SystemExit('Cannot set zwi.py username')

    try:
        keyring.set_password(key, name, password)
    except keyring.errors.PasswordSetError:
        raise SystemExit('Cannot set zwi.py username+password')

    if auth_user(key) != name:
        raise SystemExit('keyring username mismatch')
    if auth_passwd(name, key=key) != password:
        raise SystemExit('keyring password mismatch')

    return True


def check(key='zwi.py'):
    """Verify that we have established the authentication."""
    (cl, pr) = zwi_init(key=key)
    pass


def clear(key='zwi.py'):
    """Clear out any saved authentication information."""

    try:
        name = keyring.get_password(key, 'username')
    except keyring.errors.KeyringError as e:
        raise SystemExit('***keyring error:', e)

    if name is not None:
        try:
            keyring.delete_password(key, name)
        except keyring.errors.KeyringError as e:
            raise SystemExit('Trying to delete password: ***keyring error:', e)

        try:
            keyring.delete_password(key, 'username')
        except keyring.errors.KeyringError as e:
            raise SystemExit('Trying to delete username: ***keyring error:', e)
        pass
    return


def zwi_init(zid='me', key='zwi.py'):
    """Initialise communications with Zwift API."""
    global _zwi_auth_cache

    if zid in _zwi_auth_cache:
        v = _zwi_auth_cache[zid]
        return v[0], v[1]

    name = auth_user(key)
    if name:
        password = auth_passwd(name, key)
    else:
        raise SystemExit('User name not set -- re-run `auth`.')

    try:
        cl = Client(name, password)
        pr = cl.get_profile()
        pr.check_player_id()
        debug(1, f'player_id: {pr.player_id}')
        _zwi_auth_cache[zid] = [cl, pr]
        return cl, pr
    except urllib3.exceptions.HTTPError as e:
        raise SystemExit(f'Cannot connect to Zwift: {e}')
    except ConnectionError as e:
        raise SystemExit(f'Cannot connect to Zwift: {e}.')
    except Exception as e:
        print('Error:', e)
        raise SystemExit(f'Authentication failure for user {name}.')
    pass


class DataBase(object):
    cache = {}  # DB universe

    def __init__(self, path=None, reset=False, create=False):
        self._path = path
        self._cur = None

        # programming error if extant
        assert path is not None
        assert path not in DataBase.cache

        self._db = DataBase.__db_connect(path, reset, create)
        assert self._db
        DataBase.cache[path] = self
        pass

    @staticmethod
    def __db_connect(path, reset=False, create=False):
        """Setup DB for access."""

        # require creation of new DB to be explicit
        if not create and not os.path.isfile(path):
            raise SystemExit(f'Database file {path} does not exist.')

        if reset and os.path.isfile(path):
            os.remove(path)
            pass

        if reset or path not in DataBase.cache:
            db = sq.connect(path)
            pass
        return db

    @classmethod
    def db_connect(cls, path=None, reset=False, create=False):
        """Connect to a database."""
        path = get_zpath(mkdir=create) if path is None else path

        if path not in cls.cache:
            return DataBase(path=path, reset=reset, create=create)

        obj = cls.cache[path]
        if reset:   # reset extand DB, retaining object
            obj._db = cls.__db_connect(path, reset=reset, create=create)
            pass
        return obj

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
        sel = ''.join("SELECT name FROM sqlite_master",
                      f" WHERE type='table' AND name='{name}';")
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
        return self.execute(f'DROP TABLE IF EXISTS {name};')

    def create_table(self, name, cols):
        _c = ', '.join(cols)
        exe = f'CREATE TABLE IF NOT EXISTS {name}({_c});'
        self.execute(exe)
        return

    def row_insert(self, name, cols, vals):
        debug(2, f'{cols=}')
        debug(2, f'{vals=}')
        _c = ', '.join(cols)
        _v = ', '.join(vals)
        exe = f'INSERT INTO {name} ({_c}) VALUES({_v});'
        self.execute(exe)
        self.commit()
        return

    def row_replace(self, name, cols, vals):
        debug(2, f'{cols=}')
        debug(2, f'{vals=}')
        _c = ', '.join(cols)
        _v = ', '.join(vals)
        exe = f'REPLACE INTO {name} ({_c}) VALUES({_v});'
        self.execute(exe)
        self.commit()
        return

    def row_delete(self, name, col, val):
        debug(2, f'row_delete: {name=} {col=} {val=}')
        exe = f'DELETE FROM {name} WHERE {col} = {val};'
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
        if self._cur:
            self._cur.close()
            del self._cur
            self._cur = None
            pass
        if self._db:
            self._db.close()
            del self._db
            self._db = None
            pass
        assert self._path in DataBase.cache
        del DataBase.cache[self._path]
        pass
    pass


@dataclass
class ZwiBase(object):
    """base class for Zwi @dataclass objects."""

    def difference(self, other, ignore=[]):
        if isinstance(other, self.__class__):
            rv = self._diff(other, {}, ignore)
        else:
            rv = False
            pass
        self._last_difference = rv
        self._last_ignored = ignore
        return rv

    @property
    def last_difference(self):
        return self._last_difference

    def __eq__(self, other):
        rv = self.difference(other, ignore=[])
        if isinstance(rv, bool):
            return rv
        return (len(rv) == 0)

    def __ne__(self, other):
        return not self.__eq__(other)

    def _diff(self, other, d, ignore=[]):
        """Return the set of differences."""
        debug(2, f'diff: {self=}\ndiff: {other=}\ndiff: {d=}')

        for x in fields(self):
            if x.name in ignore:
                pass
            elif x.type in (int, str, bool):
                a0 = getattr(self, x.name)
                a1 = getattr(other, x.name)
                if a0 != a1:
                    d[x.name] = (a0, a1)
                    pass
                pass
            elif isinstance(x.type(), ZwiBase):
                f0 = getattr(self, x.name)
                f1 = getattr(other, x.name)
                if f0 is not None and f1 is not None:
                    rv = f0._diff(f1, {}, ignore)
                    if len(rv) > 0:
                        d[x.name] = rv
                        pass
                    pass
                elif f0 is None and f1 is None:
                    pass
                else:
                    d[x.name] = (f'{f0 is None}', f'{f1 is None}')
                    pass
                pass
            pass
        return d

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
        """Assign values from a supplied dict().
        Typically, the input here will come from a Zwift.com query,
        so we must be strict in mapping the results to something which will
        read the same after we write/read thru the DB.
        """
        if x.name in arg:
            debug(2, f'{x.name=} {x.type=} {arg[x.name]=}')
            if x.type is int and arg[x.name] is None:
                # Need to map these to zero here.
                setattr(f, x.name, 0)
            elif x.type is int:
                setattr(f, x.name, int(arg[x.name]))
            elif x.type is bool:
                # XXX: not sure here...
                setattr(f, x.name, int(arg[x.name]))
            elif x.type is str:
                # force to a string:
                setattr(f, x.name, str(arg[x.name]))
            elif isinstance(x.type(), ZwiBase):
                # we expect that f.<value> here is a suitable dict
                f0 = getattr(f, x.name)
                if f0 is not None and x.name in arg:
                    debug(2, f'dict: {f0=} {arg[x.name]=}')
                    f0.traverse(ZwiBase.from_dict, arg[x.name])
                else:
                    raise SystemExit('oops')
                pass
            else:
                raise SystemExit(f'Unexpected type: {x.type=}')
            pass
        return arg

    @staticmethod
    def to_dict(f, x, arg):
        """Assing values to a supplied dict().
        Does not construct the dict or add any missing fields.
        """
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
        We perform a depth-first traversal.
        """
        # print(f'{x.name=} {x.type=}')
        if x.type in (int, bool):
            setattr(f, x.name, arg[0][arg[1]])
            arg[1] += 1
        elif x.type is str:
            setattr(f, x.name, arg[0][arg[1]])
            arg[1] += 1
        elif isinstance(x.type(), ZwiBase):
            # decide what we need the recursion to do:
            f0 = getattr(f, x.name)
            debug(2, f'from_seq: {x.name=} {f0}')
            if f0 is not None:
                return f0.traverse(f0.from_seq, arg)
                pass
            debug(0, f'from_seq: {x.name=} {f0}')
            raise SystemExit('logic error')
        else:
            raise SystemExit(f'Unexpected type: {x.type=}')
        return arg

    pass


@dataclass
class ZwiFollowers(ZwiBase):
    def __eq__(self, other):
        rv = self.difference(other, ignore=['userAgent', 'addDate', 'delDate'])
        if isinstance(rv, bool):
            return rv
        return (len(rv) == 0)

    def __ne__(self, other):
        return not self.__eq__(other)

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
        if isinstance(data, tuple) or isinstance(data, list):
            # assumed to be the internal format
            e = ZwiFollowers()
            e.traverse(ZwiBase.from_seq, [data, 0])
            return e
        raise Exception(f'funny type ({type(data)=}) of {data!r}')

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
        if isinstance(data, tuple) or isinstance(data, list):
            # assumed to be the internal format
            e = ZwiFollowers()
            e.traverse(ZwiBase.from_seq, [data, 0])
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


@dataclass
class ZwiProfile(ZwiBase):
    def __eq__(self, other):
        rv = self.difference(other, ignore=['addDate', 'delDate'])
        if isinstance(rv, bool):
            return rv
        return (len(rv) == 0)

    def __ne__(self, other):
        return not self.__eq__(other)

    id: int = 0
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

    address: str = None,
    age: int = 0,
    bodyType: int = 0,
    connectedToStrava: bool = False,
    connectedToTrainingPeaks: bool = False,
    connectedToTodaysPlan: bool = False,
    connectedToUnderArmour: bool = False,
    connectedToWithings: bool = False,
    connectedToFitbit: bool = False,
    connectedToGarmin: bool = False,
    connectedToRuntastic: bool = False,
    connectedToZwiftPower: bool = False,
    stravaPremium: bool = False,
    bt: str = None,
    dob: str = None,
    emailAddress: str = None,
    height: int = 0,
    location: str = '',
    preferredLanguage: str = '',
    mixpanelDistinctId: str = '',
    profileChanges: bool = False,
    weight: int = 0,
    b: bool = False,
    createdOn: str = '',
    source: str = '',
    origin: str = '',
    launchedGameClient: str = '',
    ftp: int = 0,
    userAgent: str = '',
    runTime1miInSeconds: int = 0,
    runTime5kmInSeconds: int = 0,
    runTime10kmInSeconds: int = 0,
    runTimeHalfMarathonInSeconds: int = 0,
    runTimeFullMarathonInSeconds: int = 0,
    cyclingOrganization: str = None,
    licenseNumber: str = None,
    bigCommerceId: str = '',
    marketingConsent: str = None,

    achievementLevel: int = 0,
    totalDistance: int = 0,
    totalDistanceClimbed: int = 0,
    totalTimeInMinutes: int = 0,
    totalInKomJersey: int = 0,
    totalInSprintersJersey: int = 0,
    totalInOrangeJersey: int = 0,
    totalWattHours: int = 0,
    totalExperiencePoints: int = 0,
    totalGold: int = 0,
    runAchievementLevel: int = 0,
    totalRunDistance: int = 0,
    totalRunTimeInMinutes: int = 0,
    totalRunExperiencePoints: int = 0,
    totalRunCalories: int = 0,
    powerSourceType: str = '',
    powerSourceModel: str = '',
    virtualBikeModel: str = '',
    numberOfFolloweesInCommon: int = 0,
    affiliate: str = None,
    avantlinkId: str = None,
    fundraiserId: str = None,

    addDate: str = f'''{datetime.now().isoformat(timespec='minutes')}'''

    @classmethod
    def from_zwift(cls, data):
        """Init from Zwift API response."""

        if isinstance(data, dict):
            # assumed to be per the Zwift format.
            e = ZwiProfile()
            e.traverse(ZwiBase.from_dict, data)
            return e
        raise Exception(f'funny type of {data!r}')

    @classmethod
    def from_seq(cls, data):
        """Init from sequence."""
        if isinstance(data, tuple) or isinstance(data, list):
            # assumed to be the internal format
            e = ZwiProfile()
            e.traverse(ZwiBase.from_seq, [data, 0])
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

    def refresh(self, pro):
        """Refresh local cached values from Zwift."""
        return pro.refresh(self)
    pass


class ZwiUser(object):
    """Zwift user model."""

    def __init__(self, db=None, drop=False, update=False, uid=None,
                 pro_update=None):
        self._db = db
        self._wers = []
        self._wees = []
        self._wers_dict = {}
        self._wees_dict = {}
        self._cols = ZwiFollowers.column_names()
        self._uid = uid
        self._cl = None
        self._pr = None
        self._pro = pro_update
        self._setup(drop, update, uid)
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

    @property
    def wees_dict(self):
        return self._wees_dict

    @property
    def wers_dict(self):
        return self._wers_dict

    def wees_iter(self):
        """Construct an iterator to produce the wees
        as ZwiFollowers objects."""
        return (ZwiFollowers.wees(x) for x in self._wees)

    def wers_iter(self):
        """Construct an iterator to produce the wers
        as ZwiFollowers objects."""
        return (ZwiFollowers.wers(x) for x in self._wers)

    def _setup(self, drop, update, uid):
        """Syncronise with the local DB version of the world."""
        if self._db is None:  # attach to the usual DB
            if uid is not None:
                # put into a different data base
                self._db = DataBase.db_connect(get_zpath(subdir=f'{uid}',
                                                         mkdir=update),
                                               create=update)
            else:
                self._db = DataBase.db_connect(create=update)
                pass
            pass

        if drop:
            self._db.drop_table('followers')
            self._db.drop_table('followees')
            pass

        def cn(pk=''):
            return ZwiFollowers.column_names(create=True, pk=pk)

        self._db.create_table('followers', cn(pk='followerId'))
        self._db.create_table('followees', cn(pk='followeeId'))

        werid = self._cols.index('followerId')
        weeid = self._cols.index('followeeId')

        if update:  # update from Zwift?
            wers = []
            wees = []
            wers_dict = {}
            wees_dict = {}
            self._slurp(wers, wers_dict, werid, 'followers')
            self._slurp(wees, wees_dict, weeid, 'followees')
            self.update(wers, wers_dict, werid, 'followers', self.wers_fac,
                        self.wers_cmp, self.wers_del)
            self.update(wees, wees_dict, weeid, 'followees', self.wees_fac,
                        self.wees_cmp, self.wees_del)
            pass

        self._slurp(self._wers, self._wers_dict, werid, 'followers')
        self._slurp(self._wees, self._wees_dict, weeid, 'followees')
        if self._pro is not None:
            cnt = 0
            for r in self._wers:
                self._pro.update(r[werid])
                verbo(0, f'\rupdate profile of followers: {cnt}', end='')
                cnt += 1
                pass
            verbo(0, '') if cnt else None

            cnt = 0
            for r in self._wees:
                self._pro.update(r[weeid])
                verbo(0, f'\rupdate profile of followees: {cnt}', end='')
                cnt += 1
                pass
            verbo(0, '') if cnt else None
            pass
        pass

    def _slurp(self, cache, ns, idx, tab):
        """Slurp in the table data."""
        g = self._db.table_rows(tab, self._cols)
        count = 0
        for r in g():
            cache.append(r)
            ns[r[idx]] = r
            count = count + 1
            verbo(1, f'\rslurped {tab}: {count}', end='')
            pass
        verbo(1, '') if count else None
        pass

    def update(self, cache, ns, idx, tab, factory, compare, delete):
        if self._pr is None:
            self._cl, self._pr = zwi_init()
            if self._uid is None:
                self._uid = self._pr.player_id
                pass
            pass

        sym = self._cols[idx]
        vec = []
        dic = {}
        start = 0
        while True:
            req = f'/api/profiles/{self._uid}/{tab}?start={start}&limit=200'
            fe = self._pr.request.json(req)
            if len(fe) == 0:
                break

            for f in fe:
                start += 1
                vec.append(f)
                dic[f[sym]] = f
                pass
            verbo(1, f'\rupdate: processed {tab}: {start}', end='')
            pass
        verbo(1, '') if start else None

        # I want to add these into the DB in historical order.
        # It appears that more recent followers are returned first above.
        vec.reverse()

        # Check to see if there are any deletions
        hdr = f'No longer in {tab}:\n'
        for r in cache:
            zid = r[idx]
            if zid not in dic.keys():
                r = factory(r)
                print(f'{hdr}      {r.profile.firstName} {r.profile.lastName}')
                hdr = ''
                delete(zid)
                pass
            pass

        start = 0
        hdr = f'Updating {tab}:\n'
        for v in vec:
            w = factory(v)
            fun = compare(w, ns)
            if fun is not None:
                print(f'{hdr}      {w.profile.firstName} {w.profile.lastName}')
                hdr = ''
                w.addDate = f'{datetime.now().isoformat(timespec="minutes")}'
                fun(tab, w.column_names(), w.column_values())
                pass
            start += 1
            verbo(1, f'\rupdate: processed {tab}: {start}', end='')
            pass
        verbo(1, '') if start else None
        return

    def wers_fac(self, v):
        o = ZwiFollowers.wers(v)
        # self._wers.append(o)
        return o

    def wees_fac(self, v):
        o = ZwiFollowers.wees(v)
        # self._wees.append(o)
        return o

    def wers_cmp(self, o0, cache):
        if o0.followerId not in cache:
            return self._db.row_insert
        o1 = ZwiFollowers.wers(cache[o0.followerId])
        if o0 == o1:
            return None
        else:
            print(f'{o0.last_difference=}')
            return self._db.row_replace
        pass

    def wees_cmp(self, o0, cache):
        if o0.followeeId not in cache:
            return self._db.row_insert
        o1 = ZwiFollowers.wees(cache[o0.followeeId])
        if o0 == o1:
            return None
        else:
            return self._db.row_replace
        pass

    def wers_del(self, fid):
        return self._db.row_delete('followers', 'followerId', fid)

    def wees_del(self, fid):
        return self._db.row_delete('followees', 'followeeId', fid)

    pass


class ZwiPro(object):
    """Zwift profiles model.
    Seems we can get profile data given user id.
    """

    def __init__(self, db=None, drop=False, update=False, create=False):
        self._db = db
        self._cols = ZwiProfile.column_names()
        self._pro = []
        self._lookup = {}
        self._cl = None
        self._pr = None
        self._setup(drop, update, create)
        pass

    def __len__(self):
        return len(self._pro)

    def __iter__(self):
        """The iterator returns the set ZwiProfile() in the self._pro cache."""
        return (ZwiProfile.from_seq(x) for x in self._pro)

    @property
    def pr(self):
        if not self._pr:
            self._cl, self._pr = zwi_init()
            pass
        return self._pr

    @property
    def cols(self):
        return self._cols

    def _setup(self, drop, update, create):
        """Syncronise with the local DB version of the world."""
        if self._db is None:  # attach to the usual DB
            self._db = DataBase.db_connect(get_zpath(fname='profile.db'),
                                           create=create)
            pass

        if drop and not create:
            self._db.drop_table('profile')
            pass

        cn = ZwiProfile.column_names(create=True, pk='id')
        self._db.create_table('profile', cn)
        self._slurp()
        pass

    def _slurp(self):
        """Slurp in the table data."""
        g = self._db.table_rows('profile', self._cols)
        count = 0
        for r in g():
            self._pro.append(r)
            id = r[0]
            assert id not in self._lookup
            self._lookup[id] = len(self._pro) - 1

            count = count + 1
            if count <= 10 and verbo_p(2):
                verbo(3, f'{r=}')
            else:
                verbo(1, f'\rslurped profile: {count}', end='')
                pass
            pass
        verbo(1 * int(count > 0), '')
        pass

    def lookup(self, zid, fetch=False):
        """Lookup `zid` in cache, converting to ZwiProfile if found.
        Inputs:
          zid   - Zwift user-id
          fetch - fetch from Zwift if not in cache (update DB)
        """
        if zid in self._lookup:
            rv = self._pro[self._lookup[zid]]
            if isinstance(rv, tuple):
                # we got this from a DB read
                return ZwiProfile.from_seq(rv)
            if isinstance(rv, dict):
                # we got this from a Zwift query
                return ZwiProfile.from_zwift(rv)
            return rv
        return self.update(zid) if fetch else None

    def fetch_profile(self, zid):
        count = 0
        while True:
            try:
                rsp = self.pr.request.json(f'/api/profiles/{zid}')
            except zwift.error.RequestException as e:
                # This is derived from BaseExeption, not Exception...
                print(f'error trying to obtain profile for {zid}: {e}')
                rsp = None
            except ConnectionError as e:
                #  retry this some #  of times
                count += 1
                if count < 8:
                    print(f'retry: {count} of Connection reset',
                          f'trying to obtain profile for {zid}: {e}')
                    continue
                raise SystemExit(
                    f'Connection reset trying to obtain profile for {zid}: {e}'
                )
            except Exception as e:
                print(f'{type(e)} {e}')
                raise SystemExit(f'Some error trying to update id {zid}.')
            return rsp
        pass

    def update(self, zid=None, force=False):
        """Update the profile for `zid` if not currently in the DB.
        If force is set, we update regardless.
        """
        zid = self.pr.player_id if zid is None else zid

        if force is False and zid in self._lookup:
            return None

        rsp = self.fetch_profile(zid)
        if rsp is None:
            return None

        new = ZwiProfile.from_zwift(rsp)
        new.addDate = f'{datetime.now().isoformat(timespec="minutes")}'
        # update cache
        rsp[self._cols.index('addDate')] = new.addDate
        if zid in self._lookup:
            self._pro[self._lookup[zid]] = rsp
        else:
            self._pro.append(rsp)
            self._lookup[zid] = len(self._pro) - 1
            pass
        self._db.row_replace('profile', new.column_names(),
                             new.column_values())
        return new

    def refresh(self, old):
        """Refresh local DB entry from Zwift."""
        assert old.id in self._lookup

        rsp = self.fetch_profile(old.id)
        if rsp is None:
            return None

        debug(1, f'/api/profiles/{old.id} => {rsp}')
        new = ZwiProfile.from_zwift(rsp)
        debug(1, f'from_zwift => {new=}')

        debug(1, f'{old=}')
        if old == new:
            return old
        else:
            debug(1, f'{old.last_difference=}')
            pass

        new.addDate = f'{datetime.now().isoformat(timespec="minutes")}'
        # update cache
        rsp[self._cols.index('addDate')] = new.addDate
        self._pro[self._lookup[old.id]] = rsp
        # update DB
        self._db.row_replace('profile', new.column_names(),
                             new.column_values())
        return new

    def delete(self, zid):
        """delete entry from local DB."""
        self._db.row_delete('profile', 'id', zid)
        pass

    class Printer():
        fmt = [
            ('date',     ('{:18.18s} ',  '{p.addDate:18.18s} ')),
            ('ZwiftID',  ('{:>8.8s} ',   '{p.id:8d} ')),
            ('FTP',      ('{:>4.4s} ',   '{p.ftp:4d} ')),
            ('level',    ('{:>5.5s} ',   '{p.achievementLevel/100.0:5.2f} ')),
            ('hours',    ('{:>6.6s} ',   '{p.totalTimeInMinutes//60:6d} ')),
            ('distance', ('{:>8.8s} ',   '{p.totalDistance:8d} ')),
            ('climbed',  ('{:>8.8s} ',   '{p.totalDistanceClimbed:8d} ')),
            ('bike',     ('{:16.16s} ',  '{p.virtualBikeModel:16.16s} ')),
            ('name',     ('{:s}',        '{p.firstName} {p.lastName}')),
        ]

        def __init__(self, title=None, skip=[]):
            self.line_cnt = 0
            self.title = title
            self.fmt = self.__class__.fmt
            self.fmtc = [cn for (cn, x) in self.fmt]
            for c in skip:
                if c in self.fmtc:
                    idx = self.fmtc.index(c)
                    del self.fmt[idx]
                    del self.fmtc[idx]
                    pass
                pass
            pass

        def out_hdr(self, prefix):
            """Output the header."""
            print(prefix, end='')
            for idx in range(len(self.fmtc)):
                print(self.fmt[idx][1][0].format(self.fmtc[idx]), end='')
                pass
            print('')
            pass

        def out_body(self, p, prefix):
            """Output the body."""
            print(prefix, end='')
            for idx in range(len(self.fmtc)):
                print(eval("f'" + self.fmt[idx][1][1] + "'"), end='')
                pass
            print('')

        def out(self, p, prefix=' '):
            if p is None:
                return    # accept None objects

            if self.line_cnt == 0 and self.title:
                # Emit title prior to first line.
                print(self.title)
                self.title = None
                pass

            self.line_cnt += 1
            if self.line_cnt % 32 == 1:
                self.out_hdr(' ')
                pass
            self.out_body(p, prefix)
            pass
        pass
    pass
