# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Damon Anton Permezel, all bugs revered.

import sys
import signal
import time
import zwi
from zwi import ZwiPro, ZwiUser, DataBase, get_zdir
import zwift

try:
    import click
except Exception as ex__:
    print('import error', ex__)
    raise SystemExit('please run: pip3 install click')


@click.option('-v', '--verbose', count=True)
@click.option('-d', '--debug', count=True)
@click.group()
def cli(verbose, debug):
    zwi.setup(verbose, debug)
    pass


@cli.command()
def version():
    """Return the version number of the `zwi` package."""
    print(zwi.__version__)
    return


@cli.command()
@click.option('--name', prompt='Enter Zwift username', help='Zwift username')
@click.password_option(help='Zwift password')
def auth(name, password):
    """Establish the authentication."""
    return zwi.auth(name, password)


@cli.command()
def check():
    """Verify that we have established the authentication."""
    return zwi.check()


@cli.command()
def clear():
    """Clear out any saved authentication information."""
    return zwi.clear()


@cli.command()
def wees():
    """Display followees who are not following me."""
    return followees(ZwiUser())


@cli.command()
def wers():
    """Display followers who I am not following."""
    return followers(ZwiUser())


def followees(usr):
    count = 0
    for r in usr.wees:
        d = dict(zip(usr.cols, r))
        count += 1
        boo = (d['followeeStatusOfLoggedInPlayer'] != d['followerStatusOfLoggedInPlayer'])

        if zwi.verbo_p(1):
            # dump out entire list
            print('{:4d}{}{} {}\t{} {}'.format(count, [' ', '*'][boo]
                                               , d['followeeStatusOfLoggedInPlayer']
                                               , d['followerStatusOfLoggedInPlayer']
                                               , d['firstName'], d['lastName']))
        elif boo:
            # display only those whose soc status match
            print('{:4d} {} {}\t{} {}'.format(count
                                              , d['followeeStatusOfLoggedInPlayer']
                                              , d['followerStatusOfLoggedInPlayer']
                                              , d['firstName'], d['lastName']))
            pass
        pass
    print('processed {} followees'.format(count))
    pass


def followers(usr):
    count = 0
    for r in usr.wers:
        d = dict(zip(usr.cols, r))
        count += 1
        boo = (d['followeeStatusOfLoggedInPlayer'] != d['followerStatusOfLoggedInPlayer'])

        if zwi.verbo_p(1):
            print('{:4d}{}{} {}\t{} {}'.format(count, [' ', '*'][boo]
                                               , d['followeeStatusOfLoggedInPlayer']
                                               , d['followerStatusOfLoggedInPlayer']
                                               , d['firstName'], d['lastName']))
        elif boo:
            # display only those whose soc status match
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
        rows = usr.wers
    elif wees:
        rows = usr.wees
    else:
        raise SystemExit('No table selected.')
        pass

    with sys.stdout as out:
        writer = csv.DictWriter(out, fieldnames=usr.cols)
        writer.writeheader()
        for r in rows:
            d = dict(zip(usr.cols, r))
            writer.writerow(d)
            pass
        pass
    pass


@cli.command()
def reset():
    """Reset the database, refresh followers/followees data."""
    db = DataBase.db_connect(reset=True, create=True)
    ZwiUser(db, update=True)
    ZwiPro(create=True).update(force=True)

    return 0


@cli.command()
def update():
    """Update user's follower/follee DB cache."""
    ZwiUser(update=True)
    ZwiPro(create=True).update(force=True)

    return 0


@cli.command()
@click.option('--force', is_flag=True, help='Force refresh.')
def pro_update(force):
    """Update the profile DB based on user's follower/followee DB cache."""

    if zwi.verbo_p(1):
        skip = []
    else:
        skip = ['date', 'hours', 'distance', 'climbed', 'bike']
        pass

    usr = ZwiUser()
    pro = ZwiPro(create=True)
    pr = pro.Printer(skip=skip)
    done = []

    def update(zid, force):
        old = pro.lookup(zid)
        new = pro.update(zid, force=force)
        if zwi.verbo_p(1):
            if old is not None:
                pr.out(old)
                pass
            if new is None:
                if force:   # Sometimes the update fails.
                    print(f'skipping {zid}')
                    pass
                pass
            elif old is None or old is not new and  old != new:
                pr.out(new, prefix='*')
                if old is not None:
                    zwi.verbo(2, f'{old.last_difference}')
                    pass
                pass
            pass
        pass

    for r in usr.wers:
        d = dict(zip(usr.cols, r))
        update(d['followerId'], force)
        done.append(d['followerId'])
        pass

    for r in usr.wees:
        d = dict(zip(usr.cols, r))
        if d['followeeId'] in done:
            continue
        update(d['followeeId'], force)
        pass

    return 0


@cli.command()
def pro_list():
    """List profile DB contents."""

    if zwi.verbo_p(1):
        skip = []
    else:
        skip = ['date', 'hours', 'distance', 'climbed', 'bike']
        pass

    pro = ZwiPro()
    pr = pro.Printer(skip=skip)

    for p in ZwiPro():
        pr.out(p)
        pass
    return 0


def validate_prune(ctx, param, value):
    if isinstance(value, str):
        if value  == '' or len(value) == 1 and value in 'YN':
            return value
        raise click.BadParameter('must be "Y" or "N"')
    raise click.BadParameter('funny type')


@click.option('--skip', help='skip over the first N profile entries')
@click.option('--zid', help='update just the profile entry for the given Zwift ID')
@click.option('--seek', help='seek into the list of entries up to the specified Zwift ID')
@click.option('--prune', help='auto-prune all invalid entries (Y/N)',
              type=str, callback=validate_prune, default='', prompt=False)
@cli.command()
def pro_refresh(skip, zid, seek, prune):
    """Refresh local profile DB from Zwift."""
    skip = 0 if skip is None else int(skip)

    pro = ZwiPro()
    pr = pro.Printer()
    delete = 'n' if prune == '' else prune
    count = 0

    for p in pro:
        if skip > 0:
            skip -= 1
            continue

        if zid is not None and int(zid) != int(p.id):
            continue
        if seek is not None and int(seek) != int(p.id):
            continue

        count += 1

        pr.out(p)
        q = p.refresh(pro)
        if q is None:
            # Sometimes the update fails.
            ch = delete
            while delete == 'n':
                click.echo('delete entry? [ynYN?] ', nl=False)
                ch = click.getchar()
                click.echo()
                if ch == '?':
                    click.echo('\n'.join((f"y - delete one ({p.id})",
                                          f"n - don't delete one ({p.id})",
                                          "Y - delete all failing",
                                          "N - do not delete any failing",
                                          "? - help!")))
                elif ch in 'ynYN':
                    if ch in 'YN':
                        delete = ch
                        pass
                    break
                pass
            if ch in 'yY':
                zwi.verbo(0, f'deleting {p.firstName} {p.lastName}')
                pro.delete(p.id)
                pass
            pass
        elif p is not q and p != q:
            pr.out(q, prefix='*')
            zwi.verbo(1, f'{p.last_difference}')
            pass

        if zid: break
        if seek: seek = None
        pass

    if zid and count != 1:
        raise SystemExit(f'{zid} not found in local profile DB.')
    return 0


@cli.command()
def gui():
    """ZwiView."""
    try:
        from zwi import qt_gui
        return qt_gui()
    except Exception as e:
        print('import error:', e)
        raise SystemExit(e)


@cli.command()
@click.option('--zid', prompt='Zwift user ID', help='Zwift ID to inspect')
@click.option('--update', is_flag=True,
              help='update existing DB entries from Zwift')
def inspect(zid, update):
    """Inspect Zwift user `zid` and slurp down the followers/followees."""

    if zwi.verbo_p(1):
        skip = []
    else:
        skip = ['date', 'hours', 'distance', 'climbed', 'bike']
        pass

    zwi.verbo(1, f'Inspecting user {zid}')

    pro = ZwiPro()
    pseudo = ZwiUser(uid=int(zid), update=update, pro_update=pro)
    vic = pro.lookup(zid)
    if vic is None:
        vic = pro.update(zid)
        pass
    if vic is None:
        raise SystemExit(f'Zwift user {zid} not in profiles data base.')

    pr = pro.Printer(f'followers of {vic.firstName} {vic.lastName}', skip=skip)
    for f in pseudo.wers_iter():
        pr.out(pro.lookup(f.followerId))
        pass

    pr = pro.Printer(f'followees of {vic.firstName} {vic.lastName}', skip=skip)
    for f in pseudo.wees_iter():
        pr.out(pro.lookup(f.followeeId))
        pass

    return 0


# disable this ...
# @cli.command()
def devel():
    """more development staging...."""

    usr = ZwiUser()
    pro = ZwiPro()

    # pro.update(pr.player_id)

    count = 0
    for r in usr.wees:
        d = dict(zip(usr.cols, r))
        pro.update(d['followeeId'])
        zwi.verbo(0, f'\rprocessed {d["followeeId"]}: {count}', end='')
        count += 1
        pass
    zwi.verbo(0, '')

    count = 0
    for r in usr.wers:
        d = dict(zip(usr.cols, r))
        pro.update(d['followerId'])
        zwi.verbo(0, f'\rprocessed {d["followerId"]}: {count}', end='')
        count += 1
        pass
    zwi.verbo(0, '')

    zwi.setup(1, zwi.debug_lvl)

    count = 0
    for r in pro._pro:
        d = dict(zip(pro.cols, r))
        if d['id'] == 1277086:
            continue

        print(f'{d["id"]}')
        ZwiUser(uid=d['id'], update=True, pro_update=pro)
        zwi.verbo(1, f'processed {d["id"]}: {count}')
        count += 1
        pass
    pass


@click.option('--poll', is_flag=True,
              help='poll repeatedly at specified interval')
@click.option('--sleep', type=int, default=5*60,
              help='sleep interval in seconds')
@cli.command()
def worlds(poll, sleep):
    """Display info regarding worlds."""

    if sleep < 1:
        sleep = 1

    (cl, _) = zwi.zwi_init(key='zwi.py')
    lines = 0
    while True:
        # seems like there is only one worldID?
        for i in range(1, 2):
            w = None
            p = None

            try:
                w = cl.get_world(world_id=i)
                if w:
                    p = w.players
                    pass
            except zwift.error.RequestException as e:
                zwi.debug(1, f'{i=} {e=}')
                pass

            if w and p:
                friends = 0
                for f in p['friendsInWorld']:
                    if f['followerStatusOfLoggedInPlayer'] != 'NO_RELATIONSHIP':
                        friends += 1
                        pass
                    pass

                zwi.debug(1, f'{i=} {p["worldId"]=} {p["playerCount"]=}')
                if lines % 20 == 0:
                    print('world players friends')
                    pass
                print(f'{i:5d} {p["playerCount"]:7d} {friends:7d}')
                lines += 1

                if zwi.verbosity:
                    for f in p['friendsInWorld']:
                        if f['followerStatusOfLoggedInPlayer'] != 'NO_RELATIONSHIP':
                            print(f'{f["firstName"]} {f["lastName"]}')
                            pass
                        pass
                    pass
                pass
            else:
                print(f'{i=}: no world')
                pass
            pass
        if poll:
            time.sleep(sleep)
            continue
        else:
            return 0
        pass
    pass

# disable this ...
# @cli.command()
def test():
    """Test some things...."""
    import flask
    from flask import Flask, redirect, send_file
    from markupsafe import escape

    def process(self, wrk):
        """Process completed URL fetch."""
        print(f'process: {wrk=}')
        url = wrk[0]
        pass

    def callback(cache):
        """This callback is called in the worker thread."""
        print(f'callback: {cache=}')
        cache.update(process)
        pass

    idir = get_zdir('.image-cache')
    cache = zwi.AssetCache(idir, callback)
    app = Flask(__name__)

    @app.route('/<req>')
    def root(req):
        print(f'root: {req=}')
        return escape(req)

    @app.route('/images/<img>')
    def images(img):
        print(f'images: {escape(img)}')

        try:
            fna = cache.load('https://static-cdn.zwift.com/prod/profile/' + img, {})
            if fna:
                print(f'cache.load: => {fna}')
                return flask.send_file(fna,
                                       as_attachment=False,
                                       download_name=f'{img}.jpg',
                                       mimetype='image/jpeg')
            else:
                return flask.redirect('https://static-cdn.zwift.com/prod/profile/' + img, code=307)
        except Exception as ex:
            print(f'/images/{escape(img)}: {ex=}')
            return flask.Response(f'/images/{escape(img)}: {ex=}')
        pass

    app.run()

    return 0


def keyboardInterruptHandler(sig, frame):
    print(f'KeyboardInterrupt (signal: {sig}) has been caught. Cleaning up.')
    sys.exit(0)


# XXX: This works, but not entirely.
# I find I have to interact with the GUI to get it to fire
# after ^C
#
signal.signal(signal.SIGINT, keyboardInterruptHandler)


def main():
    try:
        cli()
        sys.exit(0)
    except Exception as e:
        zwi.debug(2, f'{type(e)=}\n{e!r}')
        print(f'{e}')
        if zwi.debug_p(0):
            raise Exception('oops!') from e
        sys.exit(1)
    pass
