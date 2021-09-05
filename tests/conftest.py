# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.
#
import os
import pytest

@pytest.fixture(scope="session")
def home(tmpdir_factory):
    """Provide $HOME test dir for session."""
    path = tmpdir_factory.mktemp('zwi-test')
    os.environ['HOME'] = str(path)
    assert os.environ['HOME'] == str(path)
    return str(path)

    
