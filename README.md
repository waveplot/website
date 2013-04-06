This repository stores the server code for WavePlot.

The server is written in Python 2.7, and currently uses MySQL as its database.

To get this to work on your machine, you'll need to install MySQL, load up the database (not currently available - email me if you really want it), and then make two files containing passwords for a gmail account to send server mail and a MySQL account with permissions to access and edit the newly created database. The files need to be in this format:

username:password

Then, update passwords.py to point to the locations of these two files.

You'll also need to install the Python packages Flask, Flask-Script and musicbrainz-ngs and their dependencies. You might also need the waveplot images depending on whether the database is given to you populated or with empty tables.
