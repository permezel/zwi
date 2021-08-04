# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.
#
"""Some utility functions of dubious utility."""
import sys

verbosity = 0
debug_lvl = 0


class Error(Exception):
    """Error class.  Why not? Why?"""
    def __init__(self, data):
        self.data = data
        pass

    def __str__(self):
        return f'{self.data!s}'

    def __repr__(self):
        return f'{self.data!r}'

    pass


def setup(v, d):
    """Pass in the verbosity and debug levels."""
    global verbosity, debug_lvl
    verbosity = v
    debug_lvl = d
    return

def verbo_p(lvl):
    """Predicate based on verbosity level."""
    return verbosity >= lvl

def debug_p(lvl):
    """Predicate based on the debug level."""
    return debug_lvl >= lvl

def verbo(lvl, msg, end='\n'):
    """Emit a message to stderr based on verbosity level."""
    if verbo_p(lvl):
        sys.stderr.write(msg + end)
    return

def debug(lvl, msg, end='\n'):
    """Emit a message to stderr based on debug level."""
    if debug_p(lvl):
        sys.stderr.write(msg + end)
    return

def error(data):
    """Raise an error indication."""
    debug(9, f'error: {data!s}')
    sys.stderr.write(f'error: {data!s}\n')
    raise SystemExit(data)

def warn(data):
    """Issue a warning message."""
    sys.stderr.write(f'warning: {data!s}\n')
    return
