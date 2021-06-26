#!/usr/bin/env python3
#
# I follow all those who do not follow themselves.  Who follows me?
#
#
# Usage: ./zwi.py --help
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.
#
from zwift import Client
import keyring
import click
import sys

@click.group()
def cli():
    pass

@cli.command()
@click.option('--name', prompt='Enter Zwift username', help='Zwift username')
@click.password_option(help='Zwift password')
def auth(name, password):
    """Establish the authentication."""
    print(name, password)
    try:
        cl = Client(name, password)
        pr = cl.get_profile()
        pr.check_player_id()
    except:
        print('Authentication failure.')
        sys.exit(1)
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
    except keyring.errors as e:
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
def wees():
    """Display followees who are not following me."""
    cl, pr = zwi_init()

    followees(pr)
    sys.exit(0)
    pass

@cli.command()
def wers():
    """Display followers who I am not following."""
    cl, pr = zwi_init()

    followers(pr)
    sys.exit(0)
    pass
    
def zwi_init():
    """Initialise communications with Zwift API."""

    try:
        name = keyring.get_password('zwi.py', 'username')
        password = keyring.get_password('zwi.py', name)
        pass
    except keyring.errors as e:
        print('***keyring error:', e)
        sys.exit(5)
        pass

    try:
        cl = Client(name, password)
        pr = cl.get_profile()
        pr.check_player_id()
        return (cl, pr)
    except:
        print('Authentication failure.')
        sys.exit(1)
        pass

    return (None, None)


def followees(pr, start=0, lim=5000):
    count = 0
    while start < lim:
        fe = pr.request.json('/api/profiles/{}/followees?start={}&limit=200'.format(pr.player_id, start))
        for f in fe:
            count += 1
            fep = f['followeeProfile']
            soc = fep['socialFacts']
            if soc['followeeStatusOfLoggedInPlayer'] != soc['followerStatusOfLoggedInPlayer']:
                print('{} {}\t{} {}'.format(soc['followeeStatusOfLoggedInPlayer']
                                            , soc['followerStatusOfLoggedInPlayer']
                                            , fep['firstName'], fep['lastName']))
                pass
            pass
        start += 200
        pass
    print('processed {} followees'.format(count))
    pass

def followers(pr, start=0, lim=5000):
    count = 0
    while start < lim:
        fe = pr.request.json('/api/profiles/{}/followers?start={}&limit=200'.format(pr.player_id, start))
        for f in fe:
            count += 1
            fep = f['followerProfile']
            soc = fep['socialFacts']
            if soc['followeeStatusOfLoggedInPlayer'] != soc['followerStatusOfLoggedInPlayer']:
                print('{} {}\t{} {}'.format(soc['followeeStatusOfLoggedInPlayer']
                                            , soc['followerStatusOfLoggedInPlayer']
                                            , fep['firstName'], fep['lastName']))
                pass
            pass
        start += 200
        pass
    print('processed {} followers'.format(count))
    pass

if __name__ == '__main__':
    cli()
    sys.exit(0)
    pass


