import MySQLdb as mdb
import collections

recordings = collections.defaultdict(int)

PASSWORD = "T36xrSxLUDpKHtfq"

con = mdb.connect('localhost', 'waveplot_user', PASSWORD, 'waveplot', use_unicode=True, charset = "utf8")
if con is not None:

    cur = con.cursor(mdb.cursors.DictCursor)

    cur.execute("SELECT recording_mbid FROM tracks LIMIT {},{}".format(0,1000))
    results = cur.fetchall()

    for result in results:
        recordings[result['recording_mbid']] += 1

    i = 1
    while len(results) == 1000:
        cur.execute("SELECT recording_mbid FROM tracks LIMIT {},{}".format(i*1000,1000))
        results = cur.fetchall()

        for result in results:
            recordings[result['recording_mbid']] += 1

        i += 1


i = 0
j = 0
for recording in recordings.items():
    sql_statement = "INSERT INTO recordings VALUES ('{}',{})".format(recording[0],recording[1])
    cur.execute(sql_statement)
    i += 1
    if i > 9:
        i = 0
        j += 10
        print j

con.commit()
con.close()

