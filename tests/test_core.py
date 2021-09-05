# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.
#
"""test zwi core"""

import os
import zwi
import pytest

def test_zdir(home):
    assert os.environ['HOME'] == home
    # verify get_zdir
    p = zwi.get_zdir(mkdir=False)
    assert p == home + os.sep + '.zwi' + os.sep
    assert not os.path.isdir(p)
    # now verify we mkdir (defaults to True)
    q = zwi.get_zdir()
    assert q == p
    assert os.path.isdir(p)
    # subdir=
    q = zwi.get_zdir(subdir='sub', mkdir=False)
    assert q == p + 'sub' + os.sep
    assert not os.path.isdir(q)
    # +mkdir
    q = zwi.get_zdir(subdir='sub')
    assert q == p + 'sub' + os.sep
    assert os.path.isdir(q)
    pass

def setup_zdir(home):
    assert os.environ['HOME'] == home
    return zwi.get_zdir()

def test_zpath(home):
    """Verify that we get a 'zwi.db'."""
    setup_zdir(home)
    p = zwi.get_zpath()
    assert p.split(os.sep)[-1] == 'zwi.db'
    pass

def test_db0(home):
    with pytest.raises(SystemExit):
        # Requires create=True
        db0 = zwi.DataBase.db_connect(path=None, reset=False, create=False)
        pass

    db1 = zwi.DataBase.db_connect(path=None, reset=False, create=True)
    db2 = zwi.DataBase.db_connect(path=None, reset=True,  create=False)
    db3 = zwi.DataBase.db_connect(path=None, reset=True,  create=True)

    assert db1 is db2
    assert db2 is db3
    pass

def test_db1(home):
    db0 = zwi.DataBase.db_connect(create=False)
    db0.close()
    assert zwi.get_zpath() not in zwi.DataBase.cache
    db1 = zwi.DataBase.db_connect(create=False)
    assert db1 is not db0
    assert db1.db
    assert db1.cursor
    assert db1.table_exists('test') is False
    pass

def test_db2(home):
    p  = zwi.get_zpath()
    db = zwi.DataBase.db_connect(create=False)
    assert db.path == p
    db.create_table('test', ['c0 int primary key', 'c1', 'c2'])
    assert db.table_exists('test')
    db.drop_table('test')
    # ... more needed here?
    pass

def test_zu0(home):
    u0 = zwi.ZwiUser()
    wers = zwi.ZwiFollowers()
    wees = zwi.ZwiFollowees()
    assert 0, wers

