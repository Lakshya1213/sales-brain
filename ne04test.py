from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE")

print("URI:", uri)
print("USERNAME:", username)
print("DATABASE:", database)

driver = GraphDatabase.driver(
    uri,
    auth=(username, password)
)

try:
    with driver.session(database=database) as session:
        result = session.run("RETURN 1 AS test")
        print(result.single()["test"])
        print("Neo4j Connected Successfully!")

except Exception as e:
    print("Connection Failed")
    print(e)

finally:
    driver.close()