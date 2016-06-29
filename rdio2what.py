#!/usr/bin/env python

## Created by astonmartin34 (https://what.cd/user.php?id=467912)
## Released under the terms of the GNU General Public License, version 3

import argparse
import csv
import getpass
import re
import requests
import time


# login url
auth_url = "https://what.cd/login.php"

# search url
api_url = "https://what.cd/ajax.php"
search_params = {"action": "browse"}
search_artist = "artistname"
search_album = "searchstr"
search_media = "media"

# comment this out to allow non-CD releases
search_params[search_media] = "CD"

# login POST request data (don't change these)
user_post = "username"
pw_post = "password"

# argparse
parser = argparse.ArgumentParser(description="Find WhatCD matches for Rdio user data")
parser.add_argument('datafile', help='the Rdio data file', metavar='data.csv')
args = parser.parse_args()

# open the CSV file
csvfile = None
try:
    csvfile = open(args.datafile, 'r')
    csvfile = csv.reader(csvfile, delimiter=',', quotechar='"')
except:
    raise SystemExit("CSV file could not be opened")

# get credentials to send with auth request
user = input("Username: ")
pw = getpass.getpass()
auth_data = {user_post: user, pw_post: pw}

# log me in
auth = requests.post(auth_url, data = auth_data, allow_redirects = False)
if auth.status_code == 200: # user / password not correct
    raise SystemExit("Login unsuccessful!")

# get the authkey and passkey from the index
index_params = {'action': 'index'}
index = requests.get(api_url, params = index_params, cookies = auth.cookies)
authkey = index.json()['response']['authkey']
passkey = index.json()['response']['passkey']

# get a list of albums from the CSV
album_list = []
for line in csvfile:
    # skip header
    if line == ['Name','Artist','Album','Track Number']:
        continue
    album_list.append([line[1], line[2]])
# want unique list of lists
album_list = [list(x) for x in set(tuple(x) for x in album_list)]

print("\nSearching for albums on What.CD...\n")

# see what What has
results = {}
noresults = []
for album in album_list:
    ## What.CD REQUIRES limiting API requests to 5 per 10 seconds
    time.sleep(2)
    search_params[search_artist] = album[0]
    search_params[search_album] = album[1]
    what_results = requests.get(api_url, params = search_params, cookies = auth.cookies)
    results_json = what_results.json()
    if results_json == [] or results_json['response']['results'] == []:
        noresults.append(album)
        continue
    formats = []
    # assumes the first match is correct!!!
    # TODO: more complicated strategy?
    for torrent in results_json['response']['results'][0]['torrents']:
        fmt_string = torrent['format']
        if fmt_string != 'FLAC':
            fmt_string = torrent['encoding']
        fmt_string = "[" + fmt_string + "]"
        formats.append(fmt_string)
        if not album[1] in results:
            results[album[1]] = [[torrent['format'], torrent['encoding'], torrent['size'], torrent['torrentId']]]
        else:
            results[album[1]].append([torrent['format'], torrent['encoding'], torrent['size'], torrent['torrentId']])
    print(album[1], " ".join(formats))

# print the results
print("\nWe found {} albums out of {} in your list. {} failures were detected.".format(len(results), len(album_list), len(noresults)))
if len(noresults) > 0:
    print_failures = input("Would you like to print out the failures? (y/N)\n")
    if print_failures == "y":
        for album in noresults:
            print(" - ".join(album))

# output torrent links if user wants
save_torrent_list = input("Would you like to save a list of torrents to a file? (y/N)\n")
if save_torrent_list == "y":
    which_fmts = input("Which formats would you like? Type any of flac, 320, v0, v2, separated by a comma.\n")
    which_fmts = [x.strip().lower() for x in which_fmts.split(',')]
    output = input("Enter an output filename:\n")
    with open(output, 'w') as f:
        for album in results:
            for fmt in which_fmts:
                album_data = None
                for torrent in results[album]:
                    if fmt in torrent[0].lower() or fmt in torrent[1].lower():
                        album_data = torrent
                        break
                if not album_data == None:
                    f.write(str(album) + " " + "https://what.cd/torrents.php?action=download&id={}&authkey={}&torrent_pass={}\n".format(album_data[3], authkey, passkey))

# calculate how much there is to download
size_flac = 0
size_320 = 0
size_v0 = 0
size_v2 = 0
for album in results:
    # only allow first result
    fmt_found = [0,0,0,0]
    for torrent in results[album]:
        if 'flac' in torrent[0].lower() and not fmt_found[0]:
            fmt_found[0] = 1
            size_flac += torrent[2]
        if '320' in torrent[1].lower() and not fmt_found[1]:
            fmt_found[1] = 1
            size_320 += torrent[2]
        if 'v0' in torrent[1].lower() and not fmt_found[2]:
            fmt_found[2] = 1
            size_v0 += torrent[2]
        if 'v2' in torrent[1].lower() and not fmt_found[3]:
            fmt_found[3] = 1
            size_v2 += torrent[2]
print("\nTotal data:")
print("FLAC:", "{:.2f} GB".format(size_flac / 10**9))
print("MP3 320", "{:.2f} GB".format(size_320 / 10**9))
print("MP3 V0", "{:.2f} GB".format(size_v0 / 10**9))
print("MP3 V2", "{:.2f} GB".format(size_v2 / 10**9))

# DL torrents if user wants them
save_torrents = input("\nWould you like to download .torrent files? (y/N)\n")
if save_torrents == "y":
    which_fmts = input("Which formats would you like? Type any of flac, 320, v0, v2, separated by a comma.\n")
    which_fmts = [x.strip().lower() for x in which_fmts.split(',')]
    print("Downloading files...")
    for fmt in which_fmts:
        for album in results:
            for torrent in results[album]:
                if fmt in torrent[0].lower() or fmt in torrent[1].lower():
                    ## What.CD REQUIRES limiting API requests to 5 per 10 seconds
                    time.sleep(2)
                    torrent_url = "https://what.cd/torrents.php?action=download&id={}&authkey={}&torrent_pass={}".format(torrent[3], authkey, passkey)
                    torrent_file = requests.get(torrent_url, cookies = auth.cookies)
                    filename = ""
                    # complicated process to get a reasonable filename
                    # usually the server will send it in the content-disposition header
                    try:
                        content_disposition = torrent_file.headers['content-disposition']
                        filename = re.findall("filename=(.+)", content_disposition)[0].strip('"')
                    except:
                        filename = (album + " " + fmt + ".torrent")
                    with open(filename, 'wb') as output:
                        output.write(torrent_file.content)
                        print("Downloaded", filename)
                    break
