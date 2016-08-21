import psycopg2
import csv

try:
    conn = psycopg2.connect("dbname='rcfbpoll' user='sirgippy' host='localhost' password='password'")
except:
    print "I am unable to connect to the database"

cur = conn.cursor()

with open('./csvs/new_voters.txt', 'rb') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        cur.execute("""SELECT id FROM poll_user WHERE username=%s""", row)
        result = cur.fetchone()
        if result is not None:
            user_id = result[0]
        else:
            cur.execute("""INSERT INTO poll_user(username) VALUES (%s)""", row)
            cur.execute("""SELECT id FROM poll_user WHERE username=%s""", row)
            user_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO poll_userrole(role,user_id) VALUES (%s,%s)""", ('voter', user_id))

conn.commit()
cur.close()
conn.close()
