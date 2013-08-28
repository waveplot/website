#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import division, absolute_import
import MySQLdb as db

import threading
import requests
import time
import json

from collections import OrderedDict, deque

from waveplot.passwords import passwords
import waveplot.utils

class LookupThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.db_con = db.connect(host = "localhost", user = passwords['mysql']['username'], passwd = passwords['mysql']['password'], db = 'waveplot', use_unicode = True, charset = "utf8")
        self.recent_release_lookups = OrderedDict()
        self.recent_recording_lookups = deque()
        self._stop = threading.Event()

    def _add_or_update_artist_credit_(self, release_artist_credits):
        cur = waveplot.utils.get_cursor(self.db_con)

        artist_credit_name = u''.join((artist_credit[u'name'] + artist_credit[u'joinphrase']) for artist_credit in release_artist_credits)

        cur.execute("SELECT id FROM artist_credits WHERE name=%s", (artist_credit_name,))

        # Fill possible matches with all ids that match the initial conditions
        rows = cur.fetchall()

        # If there are no matches left, make a new credit and create artist-artist credit links
        # If there are matches, update all artist-artist credit links

        if not rows:
            cur.execute("INSERT INTO artist_credits (name) VALUES(%s)", (artist_credit_name,))
            self.db_con.commit()
            cur.execute("SELECT id FROM artist_credits WHERE name=%s", (artist_credit_name,))
            artist_credit_id = cur.fetchall()[0][0]
        else:
            artist_credit_id = rows[0][0]

        for i in xrange(0, len(release_artist_credits)):
            artist_credit = release_artist_credits[i]
            cur.execute("REPLACE artists VALUES(%s,%s)", (artist_credit[u'artist'][u'id'], artist_credit[u'artist'][u'name']))

            query = "REPLACE artist_artist_credit VALUES(%s,%s,%s,%s,%s)"
            data = (artist_credit_id, artist_credit[u'artist'][u'id'], artist_credit[u'name'], i, artist_credit[u'joinphrase'])

            cur.execute(query, data)
            self.db_con.commit()

        # Finally, update the artist credit picture using the google result if it's not user set (currently unimplemented)
        # Return the credit id
        return artist_credit_id

    def _cache_releases_(self):
        cur = waveplot.utils.get_cursor(self.db_con)

        cur.execute("SELECT mbid FROM releases WHERE cached_title IS NULL LIMIT 1000")

        results = cur.fetchall()

        for result in results:
            try:
                r = requests.get("http://musicbrainz.org/ws/2/release/{}?inc=recordings&fmt=json".format(result[0]))

                release_data = r.json()

                if result[0] == release_data[u'id']:
                    cur.execute("UPDATE releases SET cached_title=%s WHERE mbid=%s", (release_data[u'title'], result[0]))
                else:
                    # Check that this release isn't already separately in the table.
                    cur.execute("SELECT mbid FROM releases WHERE mbid=%s", (release_data[u'id'],))
                    if cur.fetchone() is not None:
                        # Delete this recording
                        cur.execute("DELETE FROM releases WHERE mbid=%s", (result[0],))
                    else:
                        # Update this recording
                        cur.execute("UPDATE releases SET cached_title=%s,mbid=%s WHERE mbid=%s", (release_data[u'title'], release_data[u'id'], result[0]))

                    # Redirect waveplot
                    cur.execute("UPDATE waveplots SET release_mbid=%s WHERE release_mbid=%s", (release_data[u'id'], result[0]))
                self.db_con.commit()

                for medium in release_data[u'media']:
                    for track in medium[u'tracks']:
                        # Update track and recording information
                        recording = track[u'recording']
                        cur.execute("UPDATE recordings SET cached_title=%s WHERE mbid=%s", (recording[u'title'], recording[u'id']))

                        # Check that recording and track mbids are correct for disc/track pair
                        # cur.execute("SELECT * FROM waveplots WHERE recording_mbid=%s AND release_mbid=%s",(recording[u'id'],release_data[u'id']))
                        # cur.execute("UPDATE tracks SET cached_title=%s WHERE mbid=%s",(track[u'title'],track[u'id']))

                        self.db_con.commit()

                time.sleep(1)

                # Get artist credits! Yay!
                r = requests.get("http://musicbrainz.org/ws/2/release/{}?inc=artist-credits&fmt=json".format(result[0]))
                release_artist_credits = r.json()[u'artist-credit']

                artist_credit_id = self._add_or_update_artist_credit_(release_artist_credits)
                cur.execute("UPDATE releases SET cached_artist_credit=%s WHERE mbid=%s", (artist_credit_id, result[0]))
                self.db_con.commit()

                time.sleep(1)

            except requests.ConnectionError:
                self.db_con.rollback()

    def _cache_recordings_(self):
        cur = waveplot.utils.get_cursor(self.db_con)

        cur.execute("SELECT mbid FROM recordings WHERE cached_title IS NULL LIMIT 1000")

        results = cur.fetchall()


        for result in results:
            try:
                r = requests.get("http://musicbrainz.org/ws/2/recording/{}?fmt=json".format(result[0]))

                recording_data = r.json()

                if result[0] == recording_data[u'id']:
                    cur.execute("UPDATE recordings SET cached_title=%s WHERE mbid=%s", (recording_data[u'title'], result[0]))
                else:
                    # Check that this recording isn't already separately in the table.
                    cur.execute("SELECT mbid FROM recordings WHERE mbid=%s", (recording_data[u'id'],))
                    if cur.fetchone() is not None:
                        # Delete this recording
                        cur.execute("DELETE FROM recordings WHERE mbid=%s", (result[0],))
                    else:
                        # Update this recording
                        cur.execute("UPDATE recordings SET cached_title=%s,mbid=%s WHERE mbid=%s", (recording_data[u'title'], recording_data[u'id'], result[0]))

                    # Redirect waveplot
                    cur.execute("UPDATE waveplots SET recording_mbid=%s WHERE recording_mbid=%s", (recording_data[u'id'], result[0]))

                self.db_con.commit()
                time.sleep(1)
            except requests.ConnectionError:
                pass

    def run(self):
        while not self._stop.is_set():
            print "Running caching loop!"
            # Cache any releases missing data, and correct merges
            self._cache_releases_()

            # Cache any recordings missing data, and correct merges
            self._cache_recordings_()

            time.sleep(60)

    def stop(self):
        self._stop.set()

# Unused stuff - will be needed for recaching support.
    def unused(self):
        try:
            if release_mbid not in self.recent_release_lookups:
                release_response = requests.get("http://musicbrainz.org/ws/2/release/{}?inc=artist-credits&fmt=json".format(release_mbid))


            if recording_mbid not in self.recent_recording_lookups:
                recording_response = requests.get("http://musicbrainz.org/ws/2/recording/{}?fmt=json".format(recording_mbid))

        except requests.ConnectionError:
            success = False

        else:
            release_data = recording_data = None

            if release_mbid in self.recent_release_lookups:
                release_data = self.recent_release_lookups[release_mbid]
            elif release_response.status_code == 200:
                release_data = release_response.json()

                aartist_credit = u""
                for c in release_data["artist-credit"]:
                    aartist_credit += c["artist"]["name"]

                    if "joinphrase" in c:
                        aartist_credit += c["joinphrase"]

                self.recent_release_lookups[release_mbid] = release_data = (release_data["title"], aartist_credit)
                cur.execute("UPDATE releases SET cached_name=%s, cached_artist=%s WHERE mbid=%s", (release_data[0], release_data[1], release_mbid))

                if len(self.recent_release_lookups) > 100:
                    self.recent_release_lookups.popitem(last = False)

            if recording_mbid not in self.recent_recording_lookups:
                if recording_response.status_code == 200:
                    recording_data = recording_response.json()

                    self.recent_recording_lookups.append(recording_mbid)
                    if len(self.recent_recording_lookups) > 10000:
                        self.recent_recording_lookups.popleft()

                if (release_data is not None) and (recording_data is not None):
                    recording_name = recording_data["title"]
                    print recording_name
                    cur.execute("UPDATE waveplots SET cached_recording_name=%s, cached_release_name=%s, cached_release_artist=%s WHERE waveplot_uuid=%s", (recording_name, release_data[0], release_data[1], waveplot_uuid))
                else:
                    success = False

        if not success:
            self.queue.put((waveplot_uuid, release_mbid, recording_mbid))

        self.queue.task_done()
        time.sleep(delay_time)
