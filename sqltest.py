import psycopg2


conn = psycopg2.connect(
    host="127.0.0.1",
    database="postgres",
    user="postgres",
    password="postgres",
    port=5432
)

print("Connected Successfully!")
conn.close()

