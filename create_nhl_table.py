import psycopg2

conn = psycopg2.connect("host=localhost dbname=nhl_stats_201819 user=samoz password=samoz")
cur = conn.cursor()
cur.execute("""
        CREATE TABLE shots(
        num integer PRIMARY KEY,
        playerName text,
        playerID integer,
        result text,
        Xcoord float,
        Ycoord float,
        period integer,
        time text,
        shooterTeamGoals integer,
        opponentGoals integer)""")
conn.commit()


