[![logo](https://raw.githubusercontent.com/permezel/zwi/master/logo.png)](https://zwift.com/)
# zwi

Here are some small python programmes to facilitate viewing Zwift data.

# requirements

    a Zwift user account
    python3.9 or later
    pip3

# usage

The easist way to use this is to use `pip3 install` to install
everything you need. Prior to that, you should probably have done
something like: 

    ZWI_ENV=/tmp/zwi_env
    python3 --version
    python3 -m venv ${ZWI_ENV}
    . ${ZWI_ENV}/bin/activate

At this point, you will have a dedicated play area to install `zwi`
and dependencies. 

    pip3 install zwi

This will install everything required, and place two command scripts
in `${ZWI_ENV}/bin` which will be in your `${PATH}` while the
environjment is activated. 

    zwi --help

## version

    zwi version

The `version` function returns the version number of the currently
installewd `zwi` package. 

## authentication

Before you can do much of interest, you must store your authentication
information in the local key store. For OsX, this is the system
keychain.  For linux, it is something similar. 

    zwi auth --help
    zwi auth --name=guest@example.com --password=SuperSecret123
    zwi auth

You can have the `auth` programme prompt for both `name` and
`password`.  You need to enter the password twice, in that case, and
it will not be stored unless it successfully aithenticates with the
Zwift server. 

## verification

    zwi check --help
    zwi check

The `check` function will verify that the stored credentials function.
At times on MacOS, the keychain decides it doesn't like you any more
and requires you to enter your login password, twice, whenever `zwi`
access the stored user name and password.  Make sure you click on
`always allow` unless you need to practice typing your password.

## initialise/reset database

Once you are authenticated, the next step is to populate the local
database cache with information from Zwift.  `zwi` maintains state in
`${HOME}/.zwi/`.  An `sqlite3` database is used to cache the state of
the user's `followers` and `followees` lists. In addition, the
profiles of all Zwift users encountered (via the
`followers`/`followees` lists) are saved in a separate database. 

    zwi reset --help
    zwi reset

The `reset` function deletes the `${HOME}/.zwi/zwi.db` database file
if it exists, creates the `sqlite3` database, and populates the
database with the `followers` and `followees` tables. 
It will not delete the profiles database, but it will ensure that
there are profile entries for each user in the `followers` and
`followees` lists.

## update followers/followees database

    zwi update --help
    zwi -v update

The `update` function refreshes the `followers` and `followees` information.
(Currently, this function is being fleshed out.  It does not yet
report any differences. Also, it fails to process deletions.) 

## update profile database

    zwi pro-update --help
    zwi [-v] pro-update [--force]

The `pro-update` function will update the local DB profile cache using
information in the local Zwift user `followers` and `followees` DB
cache.

## list profile database entries

    zwi pro-list --help
    zwi pro-list

The profiles list can be displayed.

## bokeh

    zwibok serve [--port=#]

The `profile` database can be viewed using the `zwibok` app.
This will pop up a page on your browser allowing you to explore
various attributes of the users in the `profile` data base.
It should be more or less obvious.  Eventually I might try to write
some usage info, but as it is more or less a proof-of-concept, it
might change again soon.

Basically, it presents an X/Y plot of subsets of the data.  You can
select different data columns for X and Y.  You can adjust range
sliders to reduce the set of data points in the plot.
Male-only or female-only or both can be selected.

The cross-hairs of the cursor select users and display some more info
pertaining to the user.

## gui

    zwi gui --help
    zwi gui

The `gui` function pops up a window displaying data from the local
database copy of the Zwift `followers` and `followees` tables.
This was my second attempt at writing a gui to view some of the
data. Currently, it only displays information from the `followers` and
`followees` lists.

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

## followees

    zwi wees --help
    zwi wees

The `wees` function will check the cached followees list (them who's followed).
Any subject who is being followed but who is not reciprocating is displayed.
You will have to manually search for the user in the Zwift companion and decide what punishment to hand out.

## followers

    zwi wers --help
    zwi wers

The `wers` function will check the cached followers list and display any lacking reciprocity.
Certain users will follow you, but not respond to reciprocal follow requests, remaining forever in limbo.
One can always try unfollowing/refollowing to see if the recalcitrant is interested in reciprocity.
As above, as far as I know, one has to use the Zwift companion app to search by name.

## inspect other user's public information.

Per the Zwift privacy policy, various data are publicly accessible.  The `inspect` command
facilitates examination of the publicly available data.

    zwi inspect --help
    zwi inspect --zid=ZwiftUser
    zwi -v inspect --zid=ZwiftUser --update

## removing authentication information

The `clear` function will remove any cached user/password information from the keystore.

# development

I have been using `anaconda` on `OsX` for development.  Supposedly, this will install things
to facilitate development:

    conda env create -f environment.yml
    conda activate zwi
    flit install --symlink
    pip3 install zwift-client
    pip3 install PyQt5

# hints

When manually deleting followees, using the Zwift companion app, and
searching by name, I find it helps to type in the bits of the name
which are more likely to be unique, so as to limit the lists
presented. 

# user feedback

## issues

If you have any problems with or questions about this image, please contact me
through a [GitHub issue](https://github.com/permezel/zwi/issues).
