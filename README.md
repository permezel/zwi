[![logo](https://raw.githubusercontent.com/permezel/zwi/master/logo.png)](https://zwift.com/)
# zwi

This is a small python programme to facilitate maintaining the followers lists.

# Requirements

    python3
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

This script will store the Zwift login credentials in the system keychain.
Once authentication has been established, the login credentials need not be passed on each invocation.

## Verification

    ./zwi.py check --help
    ./zwi.py check

The `check` function will verify that the stored credentials function.

## Followees

    ./zwi.py wees --help
    ./zwi.py wees

The `wees` function will check the followees list (them who's followed). Any subject who is being followed but who is not reciprocating is displayed.
You will have to manually search for the user in the Zwift companion and decide what punishment to hand out.

## Followers

    ./zwi.py wers --help
    ./zwi.py wers

The `wers` function will check the followers list and display any lacking reciprocity.
Certain users will follow you, but not respond to reciprocal follow requests, remaining forever in limbo.
One can always try unfollowing/refollowing to see if the recalcitrant is interested in reciprocity.
As above, as far as I know, one has to use the Zwift companion app to search by name.

# Hints

When searching by name, I find it helps to type in the bits of the name which are more likely to be unique, so as to limit the lists presented.

# User Feedback

## Issues

If you have any problems with or questions about this image, please contact me
through a [GitHub issue](https://github.com/permezel/zwi/issues).
