[![logo](https://raw.githubusercontent.com/permezel/zwi/master/logo.png)](https://zwift.com/)
# zwi

Here are some small python programmes to facilitate viewing Zwift data.

# Requirements

    A Zwift account username and password
    python3
    pip3

    pip3 install zwi

# Usage

    zwi --help

## Version

    zwi version

The `version` function returns the version number of the currently installewd `zwi` package.

## Authentication

    zwi auth --help
    zwi auth

The `auth` function will store the Zwift login credentials in the system keychain.
Once authentication has been established, the login credentials need not be passed on each invocation.

## Verification

    zwi check --help
    zwi check

The `check` function will verify that the stored credentials function.
On `MacOS`, normally, you will not have to enter the login password each time.
However, whenever the `python` interpreter changes, you will have to do so twice.  Make sure you click the `always allow` button.

## Initialise/Reset database

`zwi` maintains state in `${HOME}/.zwi/`.  An `sqlite3` database is used to cache the state of the user's `followers` and `followees` lists.
In addition, the profiles of all Zwift users encountered (via the `followers`/`followees` lists) are saved in a separate database.

    zwi reset --help
    zwi reset

The `reset` function deletes the `${HOME}/.zwi/zwi.db` database file if it exists, creates the `sqlite3` database, and populates the database with the `followers` and `followees` tables.
It will not delete the profiles database.

## Update followers/followees database

    zwi update --help
    zwi -v update

The `update` function refreshes the `followers` and `followees` information.
(Currently, this function is being fleshed out.  It does not yet report any differences. Also, it fails to process deletions.)

## Update profile database

    zwi pro-update --help
    zwi [-v] pro-update [--force]

The `pro-update` function will update the local DB profile cache using information in the local Zwift user `followers` and `followees` DB cache.

## List profile database entries

    zwi pro-list --help
    zwi pro-list


## bokeh

    zwibok serve [--port=#]

The `profile` database can be viewed using the `zwibok` app.

## Gui

    zwi gui --help
    zwi gui

The `gui` function pops up a window displaying data from the local database copy of the Zwift `followers` and `followees` tables.

Key Bingings (for OSX):

    CMD-1  Switch to `followers` table.
    CMD-2  Switch to `followees` table.
    CMD-a  Toggle `auto` mode.
    CMD-n  Move to next entry.
    CMD-p  Move to previous entry.
    CMD-f  Search (not yet implemented).
    CMD-q  Quit

If `auto` mode is enabled:

    CMD-n  increase interval
    CMD-p  decrease interval

The slider at the bottom can be used to move rapidly thru the list.

For Linux, it appears the key bindings map to the CTRL key.  The menu items will indicate whatever it is.

## Followees

    zwi wees --help
    zwi wees

The `wees` function will check the cached followees list (them who's followed).
Any subject who is being followed but who is not reciprocating is displayed.
You will have to manually search for the user in the Zwift companion and decide what punishment to hand out.

## Followers

    zwi wers --help
    zwi wers

The `wers` function will check the cached followers list and display any lacking reciprocity.
Certain users will follow you, but not respond to reciprocal follow requests, remaining forever in limbo.
One can always try unfollowing/refollowing to see if the recalcitrant is interested in reciprocity.
As above, as far as I know, one has to use the Zwift companion app to search by name.

## Inspect other user's public information.

Per the Zwift privacy policy, various data are publicly accessible.  The `inspect` command
facilitates examination of the publicly available data.

    zwi inspect --help
    zwi inspect --zid=ZwiftUser
    zwi -v inspect --zid=ZwiftUser --update

## Removing authentication information

The `clear` function will remove any cached user/password information from the keystore.

# Development

I have been using `anaconda` on `OsX` for development.  Supposedly, this will install things
to facilitate development:

    conda env create -f environment.yml
    conda activate zwi
    flit install --symlink
    pip3 install zwift-client
    pip3 install PyQt5

# Hints


When manually deleting followees, using the Zwift companion app, and searching by name, I find it helps to type in the bits of the name which are more likely to be unique, so as to limit the lists presented.

# User Feedback

## Issues

If you have any problems with or questions about this image, please contact me
through a [GitHub issue](https://github.com/permezel/zwi/issues).
