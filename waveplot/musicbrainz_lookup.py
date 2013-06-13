import threading
import requests
import time
import modules.passwords as passwords
import MySQLdb as mdb

from collections import OrderedDict, deque

mysql_user = mysql_pass = ""

with open(passwords.MYSQL_PASSWORD_FILE, "r") as mysql_pass_file:
    mysql_user, mysql_pass = mysql_pass_file.read().split(":")
    mysql_pass = mysql_pass.strip('\n')

class LookupThread(threading.Thread):

    def __init__(self, lookup_queue):
        threading.Thread.__init__(self)
        self.queue = lookup_queue
        self.db_con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode = True, charset = "utf8")
        self.recent_release_lookups = OrderedDict()
        self.recent_recording_lookups = deque()

    def get_cursor(self, use_dict = False):
        try:
            if use_dict:
                result = self.db_con.cursor(mdb.cursors.DictCursor)
            else:
                result = self.db_con.cursor()

            result.execute("USE waveplot")
            self.db_con.commit()

            return result
        except mdb.OperationalError:
            self.db_con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode = True, charset = "utf8")

            if use_dict:
                result = self.db_con.cursor(mdb.cursors.DictCursor)
            else:
                result = self.db_con.cursor()

            result.execute("USE waveplot")
            self.db_con.commit()

            return result

    def run(self):
        while True:
            waveplot_uuid, delay_time = self.queue.get()[1:3]
            print waveplot_uuid,delay_time
            cur = self.get_cursor()
            cur.execute("SELECT release_mbid,recording_mbid FROM waveplots WHERE waveplot_uuid=%s", (waveplot_uuid,))
            release_mbid, recording_mbid = cur.fetchone()
            success = True

            try:
                if release_mbid not in self.recent_release_lookups:
                    release_response = requests.get("http://musicbrainz.org/ws/2/release/{}?inc=artist-credits&fmt=json".format(release_mbid))
                    time.sleep(delay_time)

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
            else:
                self.db_con.commit()

            self.queue.task_done()
            time.sleep(delay_time)
