import psycopg2
import csv

try:
    conn = psycopg2.connect("dbname='rcfbpoll' user='sirgippy' host='localhost' password='password'")
except:
    print("I am unable to connect to the database")

cur = conn.cursor()

with open('./csvs/all_voters.csv', 'rb') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        cur.execute("""INSERT INTO poll_user(username) VALUES (%s)""", row)

conn.commit()
cur.close()
conn.close()
