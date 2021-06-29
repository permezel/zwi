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
    cl, pr = zwi_init()

    followees(pr, verbose)
    sys.exit(0)
    pass

@cli.command()
@click.option('-v', '--verbose', count=True)
def wers(verbose):
    """Display followers who I am not following."""
    cl, pr = zwi_init()

    followers(pr, verbose)
    sys.exit(0)
    pass
    
def zwi_init():
    """Initialise communications with Zwift API."""

    try:
        name = keyring.get_password('zwi.py', 'username')
        password = keyring.get_password('zwi.py', name)
        pass
    except keyring.errors.KeyringError as e:
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


def followees(pr, verbose, start=0, lim=5000):
    count = 0
    while start < lim:
        fe = pr.request.json('/api/profiles/{}/followees?start={}&limit=200'.format(pr.player_id, start))
        for f in fe:
            count += 1
            fep = f['followeeProfile']
            soc = fep['socialFacts']
            boo = (soc['followeeStatusOfLoggedInPlayer'] != soc['followerStatusOfLoggedInPlayer'])

            if verbose > 0:
                # dump out entire list
                print('{:4d}{}{} {}\t{} {}'.format(count, [' ', '*'][boo]
                                                   , soc['followeeStatusOfLoggedInPlayer']
                                                   , soc['followerStatusOfLoggedInPlayer']
                                                   , fep['firstName'], fep['lastName']))
            elif boo:
                # disply only those whos soc status match
                print('{:4d} {} {}\t{} {}'.format(count
                                                  , soc['followeeStatusOfLoggedInPlayer']
                                                  , soc['followerStatusOfLoggedInPlayer']
                                                  , fep['firstName'], fep['lastName']))
                pass
            pass
        start += 200
        pass
    print('processed {} followees'.format(count))
    pass

def followers(pr, verbose, start=0, lim=5000):
    count = 0
    while start < lim:
        fe = pr.request.json('/api/profiles/{}/followers?start={}&limit=200'.format(pr.player_id, start))
        for f in fe:
            count += 1
            fep = f['followerProfile']
            soc = fep['socialFacts']
            boo = (soc['followeeStatusOfLoggedInPlayer'] != soc['followerStatusOfLoggedInPlayer'])

            if verbose > 0:
                # dump out entire list
                print('{:4d}{}{} {}\t{} {}'.format(count, [' ', '*'][boo]
                                                   , soc['followeeStatusOfLoggedInPlayer']
                                                   , soc['followerStatusOfLoggedInPlayer']
                                                   , fep['firstName'], fep['lastName']))
            elif boo:
                # disply only those whos soc status match
                print('{:4d} {} {}\t{} {}'.format(count
                                                  , soc['followeeStatusOfLoggedInPlayer']
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


