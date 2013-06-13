#!/usr/bin/env python
import os
import MySQLdb as mdb

PASSWORD = "T36xrSxLUDpKHtfq"
waveplot_dir = os.path.realpath("/home/ben/WavePlot/waveplot/static/images/waveplots")
totals = [0,0]

def waveplot_uuid_to_filename(uuid):
    return os.path.realpath(os.path.join(waveplot_dir,uuid[0:3],uuid[3:6],uuid[6:]))

con = mdb.connect('localhost', 'waveplot_user', PASSWORD, 'waveplot', use_unicode=True, charset = "utf8")
if con is None:
    print "Database error!"
    raise IOError

cur = con.cursor()

for directory, directories, filenames in os.walk(waveplot_dir):
    for filename in filenames:
        full_path = os.path.join(directory,filename)

        ext = os.path.splitext(full_path)[1]
        if ext == ".png":
            with open(full_path,"rb") as image:
                if image.read(8) != "\x89PNG\x0D\x0A\x1A\x0A":
                        os.remove(full_path)
                        totals[0] += 1

    try:
        os.removedirs(directory)
    except OSError:
        pass

cur.execute("SELECT waveplot_uuid FROM tracks")
print cur.rowcount
rows = cur.fetchall()

for row in rows:
    full_path = waveplot_uuid_to_filename(row[0])+".png"
    if not os.path.exists(full_path):
        print full_path
        totals[1] += 1

        cur.execute("DELETE FROM tracks WHERE waveplot_uuid='{}'".format(row[0]))
con.commit()
con.close()
print totals







