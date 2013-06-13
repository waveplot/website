#!/usr/bin/env python
# -*- coding: utf8 -*-
"""WavePlot

The WavePlot website.
"""

VERSION = "CITRUS"

activation_string = """
<p>Hi {}!</p>

<p>Please activate your WavePlot account using the activation link below:</p>

<p><a href="{}">{}</a></p>

<p>Many thanks for your help in building the WavePlot database!</p>"""

# Regular Python imports
import os
import os.path
import base64
import struct
import math
import random
import uuid
import time
import MySQLdb as mdb
import urllib2
import json
import zlib
import hashlib
from flask import abort, redirect, url_for
import modules.email
import modules.passwords as passwords
import Queue
import datetime
import waveplot_image
import musicbrainz_lookup

# Flask imports
from flask import Flask, request, render_template, make_response

# MusicBottle imports
from modules.MusicBrainzEntities import *

# Setup Flask
app = Flask(__name__)
app.config.from_object('waveplot.default_settings')
if os.getenv('WAVEPLOT_SETTINGS') is not None:
    app.config.from_envvar('WAVEPLOT_SETTINGS')

mysql_user = mysql_pass = ""

with open(passwords.MYSQL_PASSWORD_FILE, "r") as mysql_pass_file:
    mysql_user, mysql_pass = mysql_pass_file.read().split(":")
    mysql_pass = mysql_pass.strip('\n')

db_con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode = True, charset = "utf8")

lookup_queue = Queue.PriorityQueue(maxsize = 10000)
lookup_thread = musicbrainz_lookup.LookupThread(lookup_queue)
lookup_thread.setDaemon(True)
lookup_thread.start()

fast_lookup_queue = Queue.PriorityQueue(maxsize = 100)
fast_lookup_thread = musicbrainz_lookup.LookupThread(fast_lookup_queue)
fast_lookup_thread.setDaemon(True)
fast_lookup_thread.start()

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

def cookies_enabled(request):
    enabled = request.cookies.get('cookies', False)  # Get cookies cookie - default to False

    if not enabled:
        return False
    else:
        return True

def secsToHMS(secs):
    mins = secs // 60
    secs -= 60 * mins

    hours = mins // 60
    mins -= 60 * hours
    return "{}:{}:{}".format(hours, mins, secs)

@app.route('/', methods = ['POST', 'GET'])
def waveplot_homepage():
    resp = make_response()
    if request.method == 'POST':  # Setting cookies
        cookies = request.form['cookies']
        resp = make_response(render_template("main.html", title = "Welcome to WavePlot!", heading = "Welcome to WavePlot!", content = render_template('index.html', cookies_enabled = cookies)))
        resp.set_cookie('cookies', request.form['cookies'], max_age = 31536000)  # Set an enable cookie for one year. This is only for when the user isn't logged in - otherwise cookie preferences are stored server-side.
    else:
        resp = make_response(render_template("main.html", title = "Welcome to WavePlot!", heading = "Welcome to WavePlot!", content = render_template('index.html', cookies_enabled = True)))

    return resp

@app.route("/cookies")
def cookies():
    return render_template("main.html", title = "Cookie Notice!", heading = "Join the dark side...", content = render_template("cookies.html"))

@app.route('/enable-cookies')
def musicbottle_enablecookies():
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    resp = make_response(render_template('index.html', cookies_enabled = cookies_enabled))
    return resp

def generate_image_uuid(db_cur):
    numrows = 1
    generated_uuid = 0
    while numrows != 0:
        generated_uuid = uuid.uuid4()
        db_cur.execute("SELECT waveplot_uuid FROM waveplots WHERE waveplot_uuid='{}'".format(generated_uuid.hex))
        numrows = int(db_cur.rowcount)

    return generated_uuid

def calculate_hash(image_data):
    m = hashlib.sha1(image_data)
    return m.hexdigest()

def check_for_duplicate(db_cur, image_hash):
    db_cur.execute("SELECT waveplot_uuid FROM waveplots WHERE image_hash=%s",(image_hash,))
    if int(db_cur.rowcount) > 0:
        return db_cur.fetchone()[0]
    else:
        return None


@app.route('/submit', methods = ['POST'])
def recieve_waveplot():
    if "version" not in request.form:
        return "Need version to proceed! Upload cancelled."

    if request.form['version'] != VERSION:
        print request.form['version']
        return "Incorrect version! Upload cancelled."

    recording_mbid = request.form['recording']
    release_mbid = request.form['release']
    track = request.form['track']
    disc = request.form['disc']
    encoded_image = request.form['image']
    source = request.form['source']
    num_channels = request.form['num_channels']

    length = int(request.form['length'])
    trimmed = int(request.form['trimmed'])
    editor = request.form['editor']
    dr_level = request.form['dr_level']

    cur = get_cursor(db_con)

    image = zlib.decompress(base64.b64decode(encoded_image))

    image_hash = calculate_hash(image)
    result = check_for_duplicate(cur, image_hash)

    if result is not None:
        return result

    uuid = generate_image_uuid(cur)
    print "Generated image name: " + uuid.hex

    received_waveplot = waveplot_image.WavePlot(image, uuid.hex)

    cur.execute("SELECT id FROM editors WHERE activation_key=%s", (editor,))
    result = cur.fetchone()

    if result is None:
        return "Bad Editor ID"

    editor = result[0]

    cur.execute(
        u"INSERT INTO waveplots"
        u"(waveplot_uuid,length,trimmed_length,editor_id,recording_mbid,release_mbid,track,disc,image_hash,source,num_channels,version,dr_level)"
        u"VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (uuid.hex, secsToHMS(length), secsToHMS(trimmed), editor, recording_mbid, release_mbid, track, disc, image_hash, source, num_channels, VERSION, int(float(dr_level) * 10.0)))

    cur.execute(u"SELECT waveplot_count FROM recordings WHERE mbid=%s", (recording_mbid,))
    result = cur.fetchone()

    if result is None:
        cur.execute(u"INSERT INTO recordings VALUES (%s,%s)", (recording_mbid, 1))
    else:
        cur.execute(u"UPDATE recordings SET waveplot_count=%s WHERE mbid=%s", (result[0] + 1, recording_mbid))

    cur.execute(u"SELECT tracks, dr_level FROM releases WHERE mbid=%s", (release_mbid,))
    result = cur.fetchone()

    if result is None:
        cur.execute(u"INSERT INTO releases (mbid, dr_level) VALUES (%s,%s)", (release_mbid, int(float(dr_level) * 10.0)))
    else:
        rel_tracks = result[0]
        rel_dr_level = result[1]
        rel_dr_level *= rel_tracks
        rel_dr_level += int(float(dr_level) * 10.0)
        rel_tracks += 1
        rel_dr_level /= rel_tracks
        cur.execute(u"UPDATE releases SET dr_level=%s,tracks=%s WHERE mbid=%s", (rel_dr_level, rel_tracks, release_mbid))

    db_con.commit()

    lookup_queue.put((1, uuid.hex, 2.0))

    received_waveplot.generate_image_data()
    received_waveplot.save()

    return uuid.hex


@app.route('/lookup', methods = ['POST'])
def lookup_waveplot():
    if "version" not in request.form:
        return "Need version to proceed! Upload cancelled."

    if request.form['version'] != VERSION:
        print request.form['version']
        return "Incorrect version! Lookup cancelled."

    equality_data = {}
    length_values = ()
    trimmed_values = ()
    for key in request.form.keys():
        if key == 'track':
            equality_data['track'] = int(request.form['track'])
        elif key == 'disc':
            equality_data['disc'] = int(request.form['disc'])
        elif key == 'num_channels':
            equality_data['num_channels'] = int(request.form['num_channels'])
        elif key == 'audio_barcode':
            equality_data['audio_barcode'] = int(request.form['audio_barcode'])
        elif key == 'length':
            base_secs = int(request.form['length'])
            length_values = (secsToHMS(base_secs-3), secsToHMS(base_secs+3))
        elif key == 'length':
            base_secs = int(request.form['trimmed'])
            trimmed_values = (secsToHMS(base_secs-3), secsToHMS(base_secs+3))



    cur = get_cursor(db_con)

    #cur.execute("SELECT * FROM waveplots WHERE image_hash=%s", (image_hash,))
    #row = cur.fetchone()

    #if result is not None:
        #return json.dumps(result)

    query_str = "SELECT waveplot_uuid FROM waveplots WHERE " \
    + ("length BETWEEN TIME%s AND TIME%s AND " if len(length_values) != 0 else "") \
    + ("trimmed_length BETWEEN TIME%s AND TIME%s AND " if len(trimmed_values) != 0 else "") \
    + "=%s AND ".join(equality_data.keys()) + "=%s"
    cur.execute(query_str,length_values+trimmed_values+tuple(equality_data.values()))
    print query_str


    results = cur.fetchall()

    result_data = dict([(tupl[0],"") for tupl in results])

    for key in result_data.keys():
        with open(waveplot_image.waveplot_uuid_to_filename(key)+"_thumb","rb") as wp_file:
            result_data[key] = wp_file.read()

    return json.dumps(result_data)



@app.route("/recache/<uuid>")
def recache(uuid):
    fast_lookup_queue.put((0, uuid, 1.0))

    time.sleep(5)

    return redirect(url_for("waveplot_display", uuid = uuid))

@app.route("/extreme-dr")
def extreme_dr():
    if db_con is None:
        return False

    cur = get_cursor(db_con, use_dict = True)
    cur.execute("SELECT cached_name, cached_artist, mbid, dr_level FROM releases ORDER BY dr_level DESC LIMIT 20")
    top = cur.fetchall()

    for release in top:
#        track["image_prefix"] = waveplot_image.waveplot_uuid_to_url_suffix( track["waveplot_uuid"] )
        tmp = str(release["dr_level"])
        release["dr_level"] = tmp[:-1] + "." + tmp[-1:]

        release["short_cached_artist"] = release["cached_artist"]

        if len(release["cached_name"]) > 30:
            release["cached_name"] = release["cached_name"][0:30] + u"..."
        if len(release["cached_artist"]) > 30:
            release["short_cached_artist"] = release["cached_artist"][0:30] + u"..."

    cur.execute("SELECT cached_name, cached_artist, mbid, dr_level FROM releases ORDER BY dr_level ASC LIMIT 20")
    bottom = cur.fetchall()

    for release in bottom:
#        track["image_prefix"] = waveplot_image.waveplot_uuid_to_url_suffix( track["waveplot_uuid"] )
        tmp = str(release["dr_level"])
        release["dr_level"] = tmp[:-1] + "." + tmp[-1:]

        release["short_cached_artist"] = release["cached_artist"]

        if len(release["cached_name"]) > 30:
            release["cached_name"] = release["cached_name"][0:30] + u"..."
        if len(release["cached_artist"]) > 30:
            release["short_cached_artist"] = release["cached_artist"][0:30] + u"..."

    return render_template("main.html", title = "Extreme DR Levels", heading = "Extreme DR Levels", content = render_template("extreme_dr.html", top = top, bottom = bottom))


@app.route("/recache-artist/<name>")
def recache_artist(name):
    cur = get_cursor(db_con)
    cur.execute(u"SELECT waveplot_uuid FROM waveplots WHERE cached_release_artist LIKE %s LIMIT 1000", ("%{}%".format(name),))
    rows = cur.fetchall()

    for row in rows:
        fast_lookup_queue.put((0, row[0], 1.0))

    return redirect(url_for("waveplot_artist", name = name))

@app.route("/render/<uuid>")
def waveplot_render(uuid):
    return render_template("render.html", uuid = uuid, image_prefix = waveplot_image.waveplot_uuid_to_url_suffix(uuid))

@app.route("/waveplot/<uuid>")
def waveplot_display(uuid):
    cur = get_cursor(db_con, use_dict = True)

    cur.execute("SELECT cached_recording_name, length, recording_mbid, track, disc, cached_release_artist, trimmed_length, release_mbid, cached_release_name, source, num_channels, DATE_FORMAT(submit_date,'%H:%i UTC, %Y-%m-%d'), editor_id, dr_level FROM waveplots WHERE waveplot_uuid ='{}'".format(uuid))
    row = cur.fetchone()

    for key in row.keys():
        print key

    cur.execute("SELECT name FROM editors WHERE id='{}'".format(row['editor_id']))
    editor = cur.fetchone()['name']

    src, bitrate = row['source'].split("-")
    bitrate = str((int(bitrate) + 500) / 1000)

    row['dr_level'] = str(float(row['dr_level']) / 10.0)

    info = {
      "uuid":uuid,
      "data":row,
      "src":src.upper(),
      "bitrate":bitrate,
      "image_prefix":waveplot_image.waveplot_uuid_to_url_suffix(uuid),
      "editor":editor
      }

    return render_template("main.html", title = "\"" + info["data"]['cached_recording_name'] + "\" by " + info["data"]['cached_release_artist'], heading = "\"" + info["data"]['cached_recording_name'] + "\" by <a href=\"" + url_for('waveplot_artist', name = info["data"]['cached_release_artist']) + "\">" + info["data"]['cached_release_artist'] + "</a>", content = render_template('waveplot.html', info = info))



@app.route("/download")
def waveplot_download():
    return render_template("main.html", title = "Get Started!", heading = "Get Started!", content = render_template('download.html'))

@app.route("/recording/<mbid>")
def waveplot_recording(mbid):
    if db_con is None:
        return False

    cur = get_cursor(db_con, use_dict = True)

    cur.execute("SELECT waveplot_uuid,cached_recording_name,cached_release_artist,track,disc FROM waveplots WHERE recording_mbid='{}'".format(mbid))

    recordings = cur.fetchall()

    for recording in recordings:
        recording["image_prefix"] = waveplot_image.waveplot_uuid_to_url_suffix(recording["waveplot_uuid"])

    return render_template('main.html', title = "Recording {}".format(mbid), heading = "Recording {}".format(mbid), content = render_template("recording.html", recordings = recordings, mbid = mbid))

@app.route("/list/<page>")
def waveplot_list(page):
    if db_con is None:
        return False

    cur = get_cursor(db_con, use_dict = True)

    cur.execute("SELECT waveplot_uuid,cached_recording_name,cached_release_artist FROM waveplots ORDER BY cached_recording_name LIMIT {},{}".format(15 * (int(page) - 1), 15))

    recordings = cur.fetchall()

    for recording in recordings:
        recording["image_prefix"] = waveplot_image.waveplot_uuid_to_url_suffix(recording["waveplot_uuid"])

        if (recording["cached_recording_name"] is None) or (recording["cached_release_artist"] is None):
            lookup_queue.put((0, recording['waveplot_uuid'], 1.0))
            recording["cached_recording_name"] = "<uncached>"
            recording["cached_release_artist"] = "<uncached>"

    return render_template('main.html', title = "Recordings List", heading = "Recordings List", content = render_template("list.html", recordings = recordings, next_page = str(int(page) + 1)))

@app.route("/list_rec/<page>")
def waveplot_list_rec(page):
    if db_con is None:
        return False

    cur = get_cursor(db_con, use_dict = True)

    cur.execute("SELECT COUNT(*) FROM recordings WHERE waveplot_count > 1")
    count = cur.fetchone()["COUNT(*)"]

    cur.execute("SELECT mbid FROM recordings WHERE waveplot_count > 1 LIMIT {},{}".format(15 * (int(page) - 1), 15))

    recordings = cur.fetchall()

    return render_template('main.html', title = "Recordings List", heading = "Recordings List", content = render_template("list_rec.html", count = str(count), recordings = recordings, next_page = str(int(page) + 1)))

@app.route("/editor/<editor_id>/<page>")
def waveplot_editor(editor_id, page):
    if db_con is None:
        return False

    cur = get_cursor(db_con, use_dict = True)

    cur.execute("SELECT waveplot_uuid, cached_recording_name, cached_release_artist FROM waveplots WHERE editor_id={} ORDER BY cached_recording_name LIMIT {},{}".format(editor_id, 15 * (int(page) - 1), 15))

    recordings = cur.fetchall()

    cur.execute("SELECT name FROM editors WHERE id=%s", (editor_id,))

    editor_name = cur.fetchone()['name']

    for recording in recordings:
        recording["image_prefix"] = waveplot_image.waveplot_uuid_to_url_suffix(recording["waveplot_uuid"])

    return render_template('main.html', title = "Recordings List", heading = "Editor \"{}\"".format(editor_name), content = render_template("editor.html", editor_name = editor_name, editor_id = editor_id, recordings = recordings, next_page = str(int(page) + 1)))

@app.route("/artist/<name>")
def waveplot_artist(name):
    if db_con is None:
        return False

    cur = get_cursor(db_con, use_dict = True)

    cur.execute(u"SELECT waveplot_uuid,cached_recording_name,release_mbid,cached_release_name FROM waveplots WHERE cached_release_artist LIKE '%{}%' ORDER BY cached_release_name".format(name))

    recordings = cur.fetchall()

    for recording in recordings:
        recording["image_prefix"] = waveplot_image.waveplot_uuid_to_url_suffix(recording["waveplot_uuid"])

    return render_template('main.html', title = u"Artist: {}".format(name), heading = u"Artist: {}".format(name), content = render_template("artist.html", name = name, recordings = recordings))


@app.route('/check', methods = ['POST'])
def check_track():
    release_mbid = request.form['release']
    track_num = request.form['track']
    disc_num = request.form['disc']
    recording_mbid = request.form['recording']

    if db_con is None:
        return False

    cur = get_cursor(db_con)

    sql_string = u"SELECT waveplot_uuid FROM waveplots WHERE recording_mbid='{}' AND release_mbid='{}' AND track='{}' AND disc='{}'".format(recording_mbid, release_mbid, track_num, disc_num)
    cur.execute(sql_string)

    if int(cur.rowcount) > 0:
        return "1"
    else:
        return "0"


@app.route("/register")
def waveplot_register():
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    return render_template('main.html', title = "Register", heading = "Register as a WavePlot Editor!", content = render_template("register.html"))

def waveplot_deleteinvalid(options):
    if db_con is None:
        return False

    cur = get_cursor(db_con)
    cur.execute("SELECT waveplot_uuid FROM waveplots LIMIT 1000")
    rows = cur.fetchall()

    for row in rows:
        delete = False
        if not os.path.exists(waveplot_image.waveplot_uuid_to_filename(row[0]) + ".png"):
            delete = True
        elif options == "strict":
            if not os.path.exists("./waveplot/static/images/waveplots/" + row[0] + "_large.png"):
                delete = True
            elif not os.path.exists("./waveplot/static/images/waveplots/" + row[0] + "_small.png"):
                delete = True

        if delete:
            cur.execute("DELETE FROM waveplots WHERE waveplot_uuid='{}'".format(row[0]))

    db_con.commit()

    return "Done!"

@app.route("/delete/<uuid>")
def waveplot_delete(uuid):
    if db_con is None:
        return False

    cur = get_cursor(db_con)
    if cur.execute("DELETE FROM waveplots WHERE waveplot_uuid='{}'".format(uuid)) > 0:
        os.remove(waveplot_image.waveplot_uuid_to_filename(uuid) + ".png")
        os.remove(waveplot_image.waveplot_uuid_to_filename(uuid) + "_large.png")
        os.remove(waveplot_image.waveplot_uuid_to_filename(uuid) + "_small.png")
        db_con.commit()
        return "Done!"
    else:
        return "WavePlot not found!"

@app.route("/activate/<key>")
def waveplot_activate(key):
    if db_con is None:
        return False

    cur = get_cursor(db_con)

    cur.execute("SELECT name,activated FROM editors WHERE activation_key={}".format(key))
    row = cur.fetchone()

    if int(row[1]) == 0:
        cur.execute("UPDATE editors SET activated=1")
        db_con.commit()
        return "Thanks, " + row[0] + "! Your account is now activated."
    else:
        return "You've already activated this account!"

def generate_activation_key(db_cur):
    numrows = 1
    generated_key = 0
    while numrows != 0:
        generated_key = random.randint(0, 999999999)
        db_cur.execute("SELECT activation_key FROM editors WHERE activation_key={}".format(generated_key))
        numrows = int(db_cur.rowcount)

    return generated_key


def handle_registration_form(form):
    mb_username = form["mb_username"]
    email = form["email"]

    if (len(email) == 0) or (len(mb_username) == 0) or (request.form["email"].find("@") == -1):
        return False

    if db_con is None:
        return False

    cur = get_cursor(db_con)

    activation_key = generate_activation_key(cur)

    cur.execute("INSERT INTO editors(name,email,activation_key) VALUES('{}','{}',{})".format(mb_username, email, activation_key))

    activation_url = "http://pi.ockmore.net:19048/activate/" + str(activation_key)

    modules.email.SendEmail("ben.sput@gmail.com", email, "WavePlot Activation Required!", activation_string.format(mb_username, activation_url, activation_url))

    db_con.commit()

    return True


@app.route("/submit_form", methods = ['POST'])
def submit_form():
    if "registration" in request.form:
        if handle_registration_form(request.form):
            return "Registration Successful! Please check your supplied email address for activation instructions!"
        else:
            return "Registration Failed!"
    elif "recording_search" in request.form:
        if db_con is None:
            return "Database Error!"

        cur = get_cursor(db_con)
        cur.execute("SELECT recording_mbid FROM waveplots WHERE recording_mbid='{}'".format(request.form["mbid"]))
        row = cur.fetchone()

        if row is None:
            return "Recording not found!"

        return redirect(url_for('waveplot_recording', mbid = row[0]))
    else:
        return "Unrecognised form!"
