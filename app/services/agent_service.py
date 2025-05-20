from langchain.agents import initialize_agent, AgentType, Tool, AgentExecutor
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from app.services.faiss_store import search_faiss
from langchain.agents.conversational.base import ConversationalAgent

from neo4j import GraphDatabase
import os

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "your_password")

driver = GraphDatabase.driver(uri, auth=(user, password))

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

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

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

memory_store = {}

def get_or_create_agent(session_id: str):
    if session_id not in memory_store:
        memory_store[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

    memory = memory_store[session_id]

    print(f"\n🧠 [MEMORY for session {session_id}]")
    for msg in memory.chat_memory.messages:
        role = "User" if msg.type == "human" else "Assistant"
        print(f"{role}: {msg.content}")


    agent_chain = ConversationalAgent.from_llm_and_tools(
        llm=llm,
        tools=tools,
        memory=memory,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True
    )

    return AgentExecutor(agent=agent_chain, tools=tools, memory=memory, verbose=True)

llm = ChatOpenAI(model="gpt-4.1", temperature=0)