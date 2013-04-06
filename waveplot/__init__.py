#!/usr/bin/python2
# -*- coding: utf8 -*-
"""WavePlot

The WavePlot website.
"""

VERSION = "BANNANA"

activation_string = """
<p>Hi {}!</p>

<p>Please activate your WavePlot account using the activation link below:</p>

<p><a href="{}">{}</a></p>

<p>Many thanks for your help in building the WavePlot database!</p>"""

# Regular Python imports
from os import getenv
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
import hashlib
from flask import abort, redirect, url_for
import modules.email
import modules.passwords as passwords

# Flask imports
from flask import Flask, request, render_template, make_response

# MusicBottle imports
from modules.MusicBrainzEntities import *

# Setup Flask
app = Flask(__name__)
app.config.from_object('waveplot.default_settings')
if getenv('WAVEPLOT_SETTINGS') is not None:
    app.config.from_envvar('WAVEPLOT_SETTINGS')

mysql_user = mysql_pass = ""

with open(passwords.MYSQL_PASSWORD_FILE,"r") as mysql_pass_file:
    mysql_user,mysql_pass = mysql_pass_file.read().split(":")
    mysql_pass = mysql_pass.strip('\n')

def cookies_enabled(request):
    enabled = request.cookies.get('cookies', False) #Get cookies cookie - default to False

    if not enabled:
        return False
    else:
        return True

def secsToHMS(secs):
    mins = secs // 60
    secs -= 60*mins

    hours = mins // 60
    mins -= 60*hours
    return "{}:{}:{}".format(hours,mins,secs)

@app.route('/', methods=['POST', 'GET'])
def waveplot_homepage():
    resp = make_response()
    if request.method == 'POST': #Setting cookies
        cookies = request.form['cookies']
        resp = make_response(render_template("main.html", title="Welcome to WavePlot!", heading="Welcome to WavePlot!", content=render_template('index.html', cookies_enabled=cookies)))
        resp.set_cookie('cookies', request.form['cookies'], max_age=31536000) #Set an enable cookie for one year. This is only for when the user isn't logged in - otherwise cookie preferences are stored server-side.
    else:
        if not cookies_enabled(request):
            return redirect(url_for("cookies"))

        resp = make_response(render_template("main.html", title="Welcome to WavePlot!", heading="Welcome to WavePlot!", content=render_template('index.html', cookies_enabled=True)))

    return resp

@app.route("/cookies")
def cookies():
    return render_template("main.html", title="Cookie Notice!", heading="Join the dark side...", content=render_template("cookies.html"))

@app.route('/enable-cookies')
def musicbottle_enablecookies():
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    resp = make_response(render_template('index.html', cookies_enabled=cookies_enabled))
    return resp

def generate_image_uuid(db_cur):
    numrows = 1
    generated_uuid = 0
    while numrows != 0:
        generated_uuid = uuid.uuid4()
        db_cur.execute("SELECT waveplot_uuid FROM tracks WHERE waveplot_uuid='{}'".format(generated_uuid.hex))
        numrows = int(db_cur.rowcount)

    return generated_uuid

def calculate_hash(image_data64):
    m = hashlib.sha1(base64.b64decode(image_data64))
    return m.hexdigest()

def check_for_duplicate(db_cur,image_hash):
    print "SELECT id, waveplot_uuid FROM tracks WHERE image_hash='{}'".format(image_hash)
    db_cur.execute("SELECT id, waveplot_uuid FROM tracks WHERE image_hash='{}'".format(image_hash))
    if int(db_cur.rowcount) > 0:
        return db_cur.fetchone()[1]
    else:
        return None

def get_MB_info(release_mbid, recording_mbid):
    release_data = None

    req = urllib2.Request("http://musicbrainz.org/ws/2/release/{}?inc=artist-credits&fmt=json".format(release_mbid))
    try:
        response = urllib2.urlopen(req)
    except HTTPError:
        time.sleep(1)
        try:
            response = urllib2.urlopen(req)
        except HTTPError:
            return None

    release_data = json.loads(unicode(response.read(),encoding="utf8"))

    time.sleep(1)

    recording_data = None

    req = urllib2.Request("http://musicbrainz.org/ws/2/recording/{}?fmt=json".format(recording_mbid))
    try:
        response = urllib2.urlopen(req)
    except HTTPError:
        time.sleep(1)
        try:
            response = urllib2.urlopen(req)
        except HTTPError:
            return None

    recording_data = json.loads(unicode(response.read(),encoding="utf8"))

    aartist_credit = u""
    for c in release_data["artist-credit"]:
        aartist_credit += c["artist"]["name"]

        if "joinphrase" in c:
            aartist_credit += c["joinphrase"]

    release_name = release_data["title"]
    recording_name = recording_data["title"]

    return (recording_name,release_name,aartist_credit)

def waveplot_uuid_to_filename(uuid):
    return os.path.realpath(os.path.join("./waveplot/static/images/waveplots/",uuid[0:3],uuid[3:6],uuid[6:]))

def waveplot_uuid_to_url_suffix(uuid):
    return "images/waveplots/{}/{}/{}".format(uuid[0:3],uuid[3:6],uuid[6:])

@app.route('/submit', methods=['POST'])
def recieve_waveplot():
    if "version" not in request.form:
        return "Need version to proceed! Upload cancelled."

    if request.form['version'] != VERSION:
        return "Incorrect version! Upload cancelled."

    recording_mbid = request.form['recording']
    release_mbid = request.form['release']
    track = request.form['track']
    disc = request.form['disc']
    image = request.form['image']
    large_thumb = request.form['large_thumb']
    small_thumb = request.form['small thumb']
    source = request.form['source']
    num_channels = request.form['num_channels']

    length = int(request.form['length'])
    trimmed = int(request.form['trimmed'])
    editor = request.form['editor']
    artist_mbid = "123456789012345678901234567890123456"

    print recording_mbid

    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return "Database error!"

    cur = con.cursor()

    image_hash = calculate_hash(image)
    result = check_for_duplicate(cur,image_hash)
    if result is not None:
        print result
        # Update thumbnails
        image_name = waveplot_uuid_to_filename(result)

        if os.path.exists(image_name+"_large.png"):
            with open(image_name+"_large.png","rb+") as img_file:
                sig = img_file.read(8)
                if sig != "\x89PNG\x0D\x0A\x1A\x0A": # Check for validity
                    print "Old thumbnail invalid: {}, replacing!".format(repr(sig))
                    img_file.seek(0,0)
                    img_file.write(base64.b64decode(large_thumb))
        else:
            with open(image_name+"_large.png","wb") as img_file:
                img_file.write(base64.b64decode(large_thumb))

        if os.path.exists(image_name+"_large.png"):
            with open(image_name+"_small.png","rb+") as img_file:
                sig = img_file.read(8)
                if sig != "\x89PNG\x0D\x0A\x1A\x0A": # Check for validity
                    print "Old thumbnail invalid: {}, replacing!".format(repr(sig))
                    img_file.seek(0,0)
                    img_file.write(base64.b64decode(small_thumb))
        else:
            with open(image_name+"_small.png","wb") as img_file:
                img_file.write(base64.b64decode(small_thumb))

        return "WavePlot already in DB! Thanks!"

    image = base64.b64decode(image)

    if image[0:8] != "\x89PNG\x0D\x0A\x1A\x0A":
        return "Corrupt WavePlot uploaded!"

    uuid = generate_image_uuid(cur)
    print "Generated image name: " + uuid.hex

    cur.execute("SELECT id FROM editors WHERE activation_key={}".format(editor))
    editor = cur.fetchone()[0]

    result = get_MB_info(release_mbid,recording_mbid)
    if result is None:
        return "Could not find track on MusicBrainz, upload aborted!"
    else:
        recording_name, release_name, aartist_credit = result
        submit_string = u"INSERT INTO tracks(waveplot_uuid,length,trimmed_length,editor_id,recording_mbid,cached_recording_name,release_mbid,cached_release_name,cached_release_artist,track,disc,image_hash,source,num_channels,version) VALUES ('{}','{}','{}',{},'{}','{}','{}','{}','{}',{},{},'{}','{}',{},'{}')".format(uuid.hex,secsToHMS(length),secsToHMS(trimmed),editor,recording_mbid,recording_name.replace(u"'",u"\\'"),release_mbid,release_name.replace(u"'",u"\\'"),aartist_credit.replace(u"'",u"\\'"),track,disc,image_hash,source,num_channels,VERSION)

    print submit_string
    cur.execute(submit_string)

    con.commit()
    con.close()

    image_name = waveplot_uuid_to_filename(uuid.hex)
    image_dir = os.path.dirname(image_name)

    try:
        os.makedirs(image_dir)
    except OSError:
        pass

    if not os.path.exists(image_dir):
        return "Upload failed. Unable to store images."

    img_file = open(image_name+".png","wb")
    img_file.write(image)

    img_file.close()
    img_file = open(image_name+"_large.png","wb")
    img_file.write(base64.b64decode(large_thumb))

    img_file.close()

    img_file = open(image_name+"_small.png","wb")
    img_file.write(base64.b64decode(small_thumb))

    img_file.close()

    return "Upload successful. Thanks for your time!"

@app.route("/recache/<uuid>")
def recache(uuid):
    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor()
    cur.execute("SELECT recording_mbid, cached_recording_name, release_mbid, cached_release_name, cached_release_artist FROM tracks WHERE waveplot_uuid='{}' LIMIT 1000".format(uuid))
    row = cur.fetchone()

    result = get_MB_info(row[2],row[0])
    if result is not None:
        recording_name, release_name, aartist_credit = result

        if (recording_name != row[1]) or (release_name != row[3]) or (aartist_credit != row[4]):
            submit_string = u"UPDATE tracks SET cached_recording_name='{}',cached_release_name='{}',cached_release_artist='{}' WHERE waveplot_uuid='{}'".format(recording_name.replace(u"'",u"\\'"),release_name.replace(u"'",u"\\'"),aartist_credit.replace(u"'",u"\\'"),uuid)
            cur.execute(submit_string)

    con.commit()
    con.close()

    return redirect(url_for("waveplot_recording",uuid=uuid))

@app.route("/recache-artist/<name>")
def recache_artist(name):
    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor()
    cur.execute(u"SELECT waveplot_uuid, recording_mbid, cached_recording_name, release_mbid, cached_release_name FROM tracks WHERE cached_release_artist LIKE '%{}%' LIMIT 1000".format(name))
    rows = cur.fetchall()

    for row in rows:
      result = get_MB_info(row[3],row[1])
      if result is not None:
          recording_name, release_name, aartist_credit = result

          if (recording_name != row[2]) or (release_name != row[4]) or (aartist_credit != name):
              submit_string = u"UPDATE tracks SET cached_recording_name='{}',cached_release_name='{}',cached_release_artist='{}' WHERE waveplot_uuid='{}'".format(recording_name.replace(u"'",u"\\'"),release_name.replace(u"'",u"\\'"),aartist_credit.replace(u"'",u"\\'"),row[0])
              cur.execute(submit_string)

    con.commit()
    con.close()

    return redirect(url_for("waveplot_artist",name=name))

@app.route("/waveplot/<uuid>")
def waveplot_display(uuid):
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")

    if con is None:
        return "Database Error!"

    cur = con.cursor()

    cur.execute("SELECT cached_recording_name, length, recording_mbid, cached_release_artist, trimmed_length, release_mbid, cached_release_name, source, num_channels, DATE_FORMAT(submit_date,'%H:%i UTC, %Y-%m-%d'), editor_id FROM tracks WHERE waveplot_uuid ='{}'".format(uuid))
    row=cur.fetchone()

    cur.execute("SELECT name FROM editors WHERE id='{}'".format(row[10]))
    editor=cur.fetchone()[0]

    src, bitrate = row[7].split("-")
    bitrate = str((int(bitrate)+500)/1000)

    info = {
      "uuid":uuid,
      "data":row,
      "src":src.upper(),
      "bitrate":bitrate,
      "image_prefix":waveplot_uuid_to_url_suffix(uuid),
      "editor":editor
      }

    return render_template("main.html", title="\"" + info["data"][0] + "\" by " + info["data"][3], heading="\"" + info["data"][0] + "\" by <a href=\"" + url_for('waveplot_artist',name=info["data"][3])+"\">"+info["data"][3]+"</a>", content=render_template('waveplot.html', info=info))



@app.route("/download")
def waveplot_download():
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    return render_template("main.html", title="Get Started!", heading="Get Started!", content=render_template('download.html'))

@app.route("/recording/<mbid>")
def waveplot_recording(mbid):
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor(mdb.cursors.DictCursor)

    cur.execute("SELECT waveplot_uuid,cached_recording_name,cached_release_artist,track,disc FROM tracks WHERE recording_mbid='{}'".format(mbid))

    recordings = cur.fetchall()

    for recording in recordings:
        recording["image_prefix"] = waveplot_uuid_to_url_suffix(recording["waveplot_uuid"])

    return render_template('main.html', title = "Recording {}".format(mbid), heading = "Recording {}".format(mbid), content = render_template("recording.html", recordings = recordings))

@app.route("/list/<page>")
def waveplot_list(page):
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    print repr(mysql_pass)
    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor(mdb.cursors.DictCursor)

    cur.execute("SELECT waveplot_uuid,cached_recording_name,cached_release_artist FROM tracks ORDER BY cached_recording_name LIMIT {},{}".format(15*(int(page)-1),15))

    recordings = cur.fetchall()

    for recording in recordings:
        recording["image_prefix"] = waveplot_uuid_to_url_suffix(recording["waveplot_uuid"])

    return render_template('main.html', title = "Recordings List", heading = "Recordings List", content = render_template("list.html", recordings = recordings, next_page=str(int(page)+1)))

@app.route("/list_rec/<page>")
def waveplot_list_rec(page):
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor(mdb.cursors.DictCursor)

    cur.execute("SELECT COUNT(*) FROM recordings WHERE waveplot_count > 1")
    count = cur.fetchone()["COUNT(*)"]

    cur.execute("SELECT mbid FROM recordings WHERE waveplot_count > 1 LIMIT {},{}".format(15*(int(page)-1),15))

    recordings = cur.fetchall()

    return render_template('main.html', title = "Recordings List", heading = "Recordings List", content = render_template("list_rec.html", count=str(count), recordings = recordings, next_page=str(int(page)+1)))

@app.route("/editor/<id>/<page>")
def waveplot_editor(id,page):
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor(mdb.cursors.DictCursor)

    cur.execute("SELECT waveplot_uuid,cached_recording_name,cached_release_artist FROM tracks WHERE editor_id={} ORDER BY cached_recording_name LIMIT {},{}".format(id,15*(int(page)-1),15))

    recordings = cur.fetchall()

    cur.execute("SELECT name FROM editors WHERE id={}".format(id))

    editor_name = cur.fetchone()['name']

    for recording in recordings:
        recording["image_prefix"] = waveplot_uuid_to_url_suffix(recording["waveplot_uuid"])

    return render_template('main.html', title = "Recordings List", heading = "Recordings List", content = render_template("editor.html", editor_name = editor_name, editor_id=id, recordings = recordings, next_page=str(int(page)+1)))

@app.route("/artist/<name>")
def waveplot_artist(name):
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor(mdb.cursors.DictCursor)

    cur.execute(u"SELECT waveplot_uuid,cached_recording_name,release_mbid,cached_release_name FROM tracks WHERE cached_release_artist LIKE '%{}%' ORDER BY cached_release_name".format(name))

    recordings = cur.fetchall()

    for recording in recordings:
        recording["image_prefix"] = waveplot_uuid_to_url_suffix(recording["waveplot_uuid"])

    return render_template('main.html', title = u"Artist: {}".format(name), heading = u"Artist: {}".format(name), content = render_template("artist.html", name=name, recordings = recordings))


@app.route('/check', methods=['POST'])
def check_track():
    release_mbid = request.form['release']
    track_num = request.form['track']
    disc_num = request.form['disc']
    recording_mbid = request.form['recording']

    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor()

    sql_string = u"SELECT id FROM tracks WHERE recording_mbid='{}' AND release_mbid='{}' AND track='{}' AND disc='{}'".format(recording_mbid,release_mbid,track_num,disc_num)
    cur.execute(sql_string)

    if int(cur.rowcount) > 0:
        con.close()
        return "1"
    else:
        con.close()
        return "0"


@app.route("/register")
def waveplot_register():
    if not cookies_enabled(request):
        return redirect(url_for("cookies"))

    return render_template('main.html', title = "Register", heading = "Register as a WavePlot Editor!", content = render_template("register.html"))

def waveplot_deleteinvalid(options):
    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor()
    cur.execute("SELECT waveplot_uuid FROM tracks LIMIT 1000")
    rows = cur.fetchall()

    for row in rows:
        delete = False
        if not os.path.exists(waveplot_uuid_to_filename(row[0])+".png"):
            delete = True
        elif options == "strict":
            if not os.path.exists("./waveplot/static/images/waveplots/"+row[0]+"_large.png"):
                delete = True
            elif not os.path.exists("./waveplot/static/images/waveplots/"+row[0]+"_small.png"):
                delete = True

        if delete:
            cur.execute("DELETE FROM tracks WHERE waveplot_uuid='{}'".format(row[0]))

    con.commit()
    con.close()

    return "Done!"

@app.route("/delete/<uuid>")
def waveplot_delete(uuid):
    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor()
    if cur.execute("DELETE FROM tracks WHERE waveplot_uuid='{}'".format(uuid)) > 0:
        os.remove(waveplot_uuid_to_filename(uuid)+".png")
        os.remove(waveplot_uuid_to_filename(uuid)+"_large.png")
        os.remove(waveplot_uuid_to_filename(uuid)+"_small.png")
        con.commit()
        con.close()
        return "Done!"
    else:
        con.close()
        return "WavePlot not found!"

@app.route("/activate/<key>")
def waveplot_activate(key):
    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor()

    cur.execute("SELECT name,activated FROM editors WHERE activation_key={}".format(key))
    row = cur.fetchone()

    if int(row[1]) == 0:
        cur.execute("UPDATE editors SET activated=1")
        con.commit()
        con.close()
        return "Thanks, "+row[0]+"! Your account is now activated."
    else:
        con.close()
        return "You've already activated this account!"

def generate_activation_key(db_cur):
    numrows = 1
    generated_key = 0
    while numrows != 0:
        generated_key = random.randint(0,999999999)
        db_cur.execute("SELECT activation_key FROM editors WHERE activation_key={}".format(generated_key))
        numrows = int(db_cur.rowcount)

    return generated_key


def handle_registration_form(form):
    mb_username = form["mb_username"]
    email = form["email"]

    if (len(email) == 0) or (len(mb_username) == 0) or (request.form["email"].find("@") == -1):
        return False

    con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
    if con is None:
        return False

    cur = con.cursor()

    activation_key = generate_activation_key(cur)

    cur.execute("INSERT INTO editors(name,email,activation_key) VALUES('{}','{}',{})".format(mb_username,email,activation_key))

    activation_url = "http://pi.ockmore.net:19048/activate/"+str(activation_key)

    modules.email.SendEmail("ben.sput@gmail.com",email,"WavePlot Activation Required!", activation_string.format(mb_username,activation_url,activation_url))

    con.commit()
    con.close()

    return True


@app.route("/submit_form", methods=['POST'])
def submit_form():
    if "registration" in request.form:
        if handle_registration_form(request.form):
            return "Registration Successful! Please check your supplied email address for activation instructions!"
        else:
            return "Registration Failed!"
    elif "recording_search" in request.form:
        con = mdb.connect('localhost', mysql_user, mysql_pass, 'waveplot', use_unicode=True, charset = "utf8")
        if con is None:
            return "Database Error!"

        cur = con.cursor()
        cur.execute("SELECT recording_mbid FROM tracks WHERE recording_mbid='{}'".format(request.form["mbid"]))
        row = cur.fetchone()

        if row is None:
            return "Recording not found!"

        return redirect(url_for('waveplot_recording',mbid=row[0]))
    else:
        return "Unrecognised form!"
