rdio2what
=========

rdio2what.py is a simple script to search What.CD for albums in your Rdio collection before it shut down. You need to have exported your data from the official Rdio source for this to work. The script can give you a list of torrents to download manually, or download them automatically for you in any format you wish. It can also show you the total size of your collection in each format so that you can estimate its effect on your buffer.

Requirements
------------

**rdio2what** requires Python3. It is only tested with Python 3.5. The only additional requirement is the **requests** library. Install it with

> sudo pip install requests

How to use
----------

1. First, you will need to have downloaded your official .zip backup from Rdio. From your archive, extract the file "favorites_albumsandsongs.csv". 
2. Run the following command:

> python rdio2what.py favorites_albumsandsongs.csv

3. Type in your username and password when prompted. 
4. The script will compile a list of albums from the CSV and check What.CD for them. This will take some time, because What limits API access to 5 requests every 10 seconds.
5. The script will give you the option to save a list of all the torrents it found, in the formats you choose. This is recommended.
6. The script will give you the option to save .torrent files to the current folder in the formats you choose.
