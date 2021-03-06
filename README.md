PyMoronBot [![Stories in Ready](https://badge.waffle.io/TyranicMoron/PyMoronBot.png?label=ready&title=Ready)](https://waffle.io/TyranicMoron/PyMoronBot) [![Python 3](https://pyup.io/repos/github/TyranicMoron/PyMoronBot/python-3-shield.svg)](https://pyup.io/repos/github/TyranicMoron/PyMoronBot/) [![Updates](https://pyup.io/repos/github/TyranicMoron/PyMoronBot/shield.svg)](https://pyup.io/repos/github/TyranicMoron/PyMoronBot/)
==========

A modular IRC bot with extensive aliasing capabilities, written in Python.

Initially a language port/rewrite of [MoronBot](https://github.com/TyranicMoron/MoronBot/) (C#), but now somewhat diverged.

Features
--------
* [Alias](pymoronbot/modules/admin/Alias.py) any of the following to create new commands on-the-fly, and then alias *those* aliases to create even more
* Use [Slurp](pymoronbot/modules/utils/Slurp.py) to extract data from HTML/XML
* Use [Sub](pymoronbot/modules/utils/Sub.py) or [Chain](pymoronbot/modules/utils/Chain.py) to link multiple modules together
  * and use [Var](pymoronbot/modules/utils/Var.py) to store data for use within the same command (eg, a URL you want to slurp multiple times)
* [Follows URLs](pymoronbot/modules/automatic/URLFollow.py) posted in chat to see where they lead (following all redirects), responding with the page title and final hostname
  * with specialised follows to get extra relevant information from Imgur, KickStarter, Steam, Twitch, Twitter, and YouTube links
* Recognizes [sed-like](pymoronbot/modules/commands/Sed.py) patterns in chat and replaces the most recent match in the last 20 messages
* Also recognizes [`*correction`](pymoronbot/modules/automatic/AsterFix.py) style corrections and replaces the most likely candidate word in that user's previous message
* [AutoPasteEE](pymoronbot/modules/postprocess/AutoPasteEE.py) detects when single responses are longer than ~2 IRC messages, and submits them to paste.ee instead, replacing the response with a link
* Consistent help for any module via the [Help](pymoronbot/modules/commands/Help.py) module
* And many more (take a look in [modules](pymoronbot/modules))

All of these features can be individually enabled/disabled by loading or unloading the module that provides them

Installation Instructions
-------------------------
* Install Python 2.7+
* Clone the repo with `git clone https://github.com/TyranicMoron/PyMoronBot.git`
* Create a virtualenv to run the bot in, and activate it
* Run `pip install -r requirements.txt` to install all the requirements
* Edit [_defaults.yaml](configs/_defaults.yaml) to set the bot owner and other details
* Copy [server.yaml.example](configs/server.yaml.example) and create a server config (you'll want one of these per IRC network)

Running the Bot
---------------
Activate your virtualenv, and run `python start.py -c configs/server.yaml`

You can run `python start.py -h` for help with the command line args
