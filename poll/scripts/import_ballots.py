import psycopg2
import csv

try:
    conn = psycopg2.connect("dbname='rcfbpoll' user='sirgippy' host='localhost' password='password'")
except:
    print("I am unable to connect to the database")

cur = conn.cursor()

with open('./csvs/ballots.csv', 'rb') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        poll_year = row[0]
        poll_week = row[1]
        cur.execute("""SELECT id, close_date FROM poll_poll WHERE year=%s AND week=%s""", (poll_year, poll_week))
        poll = cur.fetchone()
        poll_id = poll[0]
        close_time = poll[1]
        username = row[2]
        cur.execute("""SELECT id FROM poll_user WHERE username=%s""", (username,))
        try:
            user_id = cur.fetchone()[0]
        except:
            print(username)
            raise ValueError("Don't recognize user.")
        poll_type = row[3]
        cur.execute("""INSERT INTO poll_ballot(poll_type,poll_id,user_id,submission_date) VALUES (%s,%s,%s,%s)""",
                    (poll_type, poll_id, user_id, close_time))
        cur.execute("""SELECT id FROM poll_ballot WHERE poll_id=%s AND user_id=%s""",
                    (poll_id, user_id))
        ballot_id = cur.fetchone()[0]
        for i in range(1, 26):
            team_handle = row[i+3]
            if team_handle == "":
                continue
            cur.execute("""SELECT id FROM poll_team WHERE handle=%s""", (team_handle,))
            try:
                team_id = cur.fetchone()[0]
            except:
                print(team_handle)
                raise ValueError("Don't recognize team.")

            cur.execute("""INSERT INTO poll_ballotentry(rank,ballot_id,team_id) VALUES (%s,%s,%s)""",
                        (i, ballot_id, team_id))

conn.commit()
cur.close()
conn.close()
