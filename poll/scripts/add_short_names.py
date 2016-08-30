import psycopg2
import csv

try:
    conn = psycopg2.connect("dbname='rcfbpoll' user='sirgippy' host='localhost' password='password'")
except:
    print "I am unable to connect to the database"

cur = conn.cursor()

with open('./csvs/short_names.csv', 'rb') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        cur.execute("""UPDATE poll_team SET short_name= %s WHERE handle = %s""", (row[1], row[0]))

conn.commit()
cur.close()
conn.close()
