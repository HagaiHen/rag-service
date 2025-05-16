from langchain.agents import initialize_agent, AgentType, Tool
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from app.services.faiss_store import search_faiss
from neo4j import GraphDatabase
import os

# Neo4j connection (read from .env or config)
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "your_password")

driver = GraphDatabase.driver(uri, auth=(user, password))
# === Define tools ===

def graph_query(query: str) -> str:
    cypher_query = f"""
    MATCH (i:Issue)-[:RELATED_TO]-(p:Product {{name: 'Product X'}})
    RETURN i.name AS issue, p.name AS product
    LIMIT 5
    """
    with driver.session() as session:
        result = session.run(cypher_query)
        return "\n".join([f"Issue: {record['issue']} for {record['product']}" for record in result])

def vector_search(query: str) -> str:
    chunks = search_faiss(query, k=3)
    return "\n".join(chunks)

# === Setup memory ===
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# === Define tools ===
tools = [
    Tool(
        name="Vector_Search",
        func=vector_search,
        description="Use to retrieve unstructured documents like support tickets and KB articles."
    ),
    Tool(
        name="Graph_Query",
        func=graph_query,
        description="Use to retrieve structured facts, relations, or multi-hop data from the Knowledge Graph."
    ),
]

# === Initialize memory-aware agent ===
llm = ChatOpenAI(model="gpt-4.1", temperature=0)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)