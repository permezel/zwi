[![logo](https://raw.githubusercontent.com/permezel/zwi/master/logo.png)](https://zwift.com/)
# zwi

This is a small python programme to facilitate maintaining the followers lists.

# Requirements

    python3 with tkinter support
    pip3
    click
    zwift-client
    keyring

    pip3 install click
    pip3 install keyring
    pip3 install zwift-client
  
# Usage

    ./zwi.py --help

## Authentication

    ./zwi.py auth --help
    ./zwi.py auth

The `auth` function will store the Zwift login credentials in the system keychain.
Once authentication has been established, the login credentials need not be passed on each invocation.

## Verification

    ./zwi.py check --help
    ./zwi.py check

The `check` function will verify that the stored credentials function.

## Initialise/Reset database

`zwi` maintains state in `${HOME}/.zwi/`.  An `sqlite3` database is used to cache the state of the user's `followers` and `followees` lists.

   ./zwi.py reset --help
   ./zwi.py reset

The `reset` function deletes the `${HOME}/.zwi/zwi.db` database file if it exists, creates the `sqlite3` database, and populates the database with the `followers` and `followees` tables.

*** Currently, this version only supports a one-time slurp of the `followers` list.

## Gui

   ./zwi.py gui --help
   ./zwi.py gui

The `gui` function pops up a window representing a desire to write more code.

Using the Zwift user login information provided (see below) the followers list is obtained and stored locally in a database.
Currently, the list is not refreshed.  Working on it.
   
## Followees

   ./zwi.py wees --help
   ./zwi.py wees

The `wees` function will check the cached followees list (them who's followed).
Any subject who is being followed but who is not reciprocating is displayed.
You will have to manually search for the user in the Zwift companion and decide what punishment to hand out.

## Followers

   ./zwi.py wers --help
   ./zwi.py wers

The `wers` function will check the cached followers list and display any lacking reciprocity.
Certain users will follow you, but not respond to reciprocal follow requests, remaining forever in limbo.
One can always try unfollowing/refollowing to see if the recalcitrant is interested in reciprocity.
As above, as far as I know, one has to use the Zwift companion app to search by name.

## Removing authentication information

The `clear` function will remove any cached user/password information from the keystore.

# Hints

When manually deleting followees, and searching by name, I find it helps to type in the bits of the name which are more likely to be unique, so as to limit the lists presented.

# User Feedback

## Issues

The OSX version of `python3` does not seem to have `tkinter` support.
I found that installing from [python.org](https://python.org/) fixed things, although I do not fully understand how or why on my particular system(s).

If you have any problems with or questions about this image, please contact me
through a [GitHub issue](https://github.com/permezel/zwi/issues).
