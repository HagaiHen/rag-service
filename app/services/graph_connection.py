# app/services/graph_connection.py

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# === Read connection details from .env ===
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://your-db-id.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

# === Create the Neo4j driver ===
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))