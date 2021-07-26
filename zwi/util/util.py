# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.
#

import sys
import os
import time
import signal

verbosity = 0
debug_lvl = 0

zwi_auth_cache = {}

def setup(v, d):
    global verbosity, debug_lvl

    verbosity = v
    debug_lvl = d
    return


def verbo_p(lvl):
    return verbosity >= lvl

def debug_p(lvl):
    return debug_lvl >= lvl

def verbo(lvl, msg):
    if verbo_p(lvl):
        sys.stderr.write(msg + '\n')
    return


def debug(lvl, msg):
    if debug_p(lvl):
        sys.stderr.write(msg + '\n')
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


