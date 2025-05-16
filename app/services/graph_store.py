from app.services.openai_llm import get_openai_completion
from app.services.graph_connection import driver
import json

import json
from app.services.openai_llm import get_openai_completion

def extract_entities_relations(chunks):
    triples = []
    for chunk in chunks:
        prompt = f"""
You are an expert information extractor.

Extract the key entities and their relationships from the following text as a JSON array of triples.

Example:
Text:
"Customer Y reported the battery overheating."
Output:
[
  {{"entity1": "Customer Y", "relation": "reported", "entity2": "battery overheating"}}
]

Text:
{chunk}

Output only the JSON array of triples.
"""

        response = get_openai_completion(prompt)

        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:].strip()
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:].strip()
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3].strip()

        try:
            extracted = json.loads(cleaned_response)
            for item in extracted:
                if isinstance(item, dict) and "entity1" in item and "relation" in item and "entity2" in item:
                    triples.append((item["entity1"], item["relation"], item["entity2"]))
        except Exception as e:
            print(f"[ERROR] Failed to parse cleaned LLM output as JSON: {e}\nCleaned Response:\n{cleaned_response}")
            continue

    print(f"[GRAPH EXTRACTION] Extracted {len(triples)} triples.")
    return triples

def parse_triples_from_response(response_text):
    lines = response_text.strip().split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if line.startswith("(") and line.endswith(")"):
            try:
                triple = eval(line)
                if isinstance(triple, tuple) and len(triple) == 3:
                    cleaned.append(triple)
            except:
                continue
    return cleaned

def insert_triples_to_neo4j(triples):
    with driver.session() as session:
        for entity1, relation, entity2 in triples:
            cypher = f"""
            MERGE (a:Entity {{name: $entity1}})
            MERGE (b:Entity {{name: $entity2}})
            MERGE (a)-[r:{relation.replace(' ', '_').upper()}]->(b)
            """
            session.run(cypher, entity1=entity1, entity2=entity2)