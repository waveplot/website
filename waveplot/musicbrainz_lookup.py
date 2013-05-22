import threading
import requests
import time
import modules.passwords as passwords
import MySQLdb as mdb

from collections import OrderedDict

mysql_user = mysql_pass = ""

with open(passwords.MYSQL_PASSWORD_FILE, "r") as mysql_pass_file:
    mysql_user, mysql_pass = mysql_pass_file.read().split(":")
    mysql_pass = mysql_pass.strip('\n')

db_con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode = True, charset = "utf8")

def get_cursor(db_con, use_dict = False):
    try:
        if use_dict:
            result = db_con.cursor(mdb.cursors.DictCursor)
        else:
            result = db_con.cursor()

        result.execute("USE waveplot")
        db_con.commit()

        return result
    except mdb.OperationalError:
        db_con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode = True, charset = "utf8")

        if use_dict:
            result = db_con.cursor(mdb.cursors.DictCursor)
        else:
            result = db_con.cursor()

        result.execute("USE waveplot")
        db_con.commit()

        return result

recent_release_lookups = OrderedDict()

class LookupThread(threading.Thread):

    def __init__(self, lookup_queue):
        threading.Thread.__init__(self)
        self.queue = lookup_queue

    def run(self):
        while True:
            waveplot_uuid, release_mbid, recording_mbid = self.queue.get()
            success = True

            try:
                if release_mbid not in recent_release_lookups:
                    release_response = requests.get("http://musicbrainz.org/ws/2/release/{}?inc=artist-credits&fmt=json".format(release_mbid))
                    time.sleep(1)

                recording_response = requests.get("http://musicbrainz.org/ws/2/recording/{}?fmt=json".format(recording_mbid))

            except requests.ConnectionError:
                success = False

            else:
                release_data = recording_data = None
                cur = get_cursor(db_con)

                if release_mbid in recent_release_lookups:
                    release_data = recent_release_lookups[release_mbid]
                elif release_response.status_code == 200:
                    release_data = release_response.json()
                    if len(recent_release_lookups) > 100:
                        recent_release_lookups.popitem(last = False)

                    aartist_credit = u""
                    for c in release_data["artist-credit"]:
                        aartist_credit += c["artist"]["name"]

                        if "joinphrase" in c:
                            aartist_credit += c["joinphrase"]

                    recent_release_lookups[release_mbid] = release_data = (release_data["title"], aartist_credit)
                    cur.execute("UPDATE releases SET cached_name=%s, cached_artist=%s WHERE mbid=%s", (release_data[0], release_data[1], release_mbid))

                if recording_response.status_code == 200:
                    recording_data = recording_response.json()

                if (release_data is not None) and (recording_data is not None):
                    recording_name = recording_data["title"]
                    cur.execute("UPDATE tracks SET cached_recording_name=%s, cached_release_name=%s, cached_release_artist=%s WHERE waveplot_uuid=%s", (recording_name, release_data[0], release_data[1], waveplot_uuid))
                else:
                    success = False

            if not success:
                self.queue.put((waveplot_uuid, release_mbid, recording_mbid))
            else:
                db_con.commit()

            self.queue.task_done()
            time.sleep(1)
