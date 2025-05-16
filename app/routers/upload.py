from fastapi import APIRouter, UploadFile, File
from app.services.file_parser import parse_file
from app.services.faiss_store import add_to_faiss
from app.services.graph_store import extract_entities_relations, insert_triples_to_neo4j
import os
from uuid import uuid4
import hashlib
import json

router = APIRouter()
UPLOAD_DIR = "app/data/documents"
HASH_RECORD_FILE = "app/data/uploaded_files.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(HASH_RECORD_FILE), exist_ok=True)

if not os.path.exists(HASH_RECORD_FILE):
    with open(HASH_RECORD_FILE, "w") as f:
        json.dump([], f)

def compute_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_duplicate(file_hash):
    with open(HASH_RECORD_FILE, "r") as f:
        hashes = json.load(f)
    return file_hash in hashes

def record_file_hash(file_hash):
    with open(HASH_RECORD_FILE, "r+") as f:
        hashes = json.load(f)
        hashes.append(file_hash)
        f.seek(0)
        json.dump(hashes, f)
        f.truncate()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    file_hash = compute_file_hash(file_path)

    if is_duplicate(file_hash):
        os.remove(file_path)
        return {"message": "File already uploaded and indexed previously."}

    with open(file_path, "rb") as f:
        file.file = f
        chunks = await parse_file(file)

    print(f"[FAISS] Indexing {len(chunks)} chunks...")
    add_to_faiss(chunks)

    print(f"[GRAPH EXTRACTION] Extracting triples from {len(chunks)} chunks...")
    triples = extract_entities_relations(chunks)
    print(f"[GRAPH EXTRACTION] Extracted {len(triples)} triples.")

    if triples:
        print("[NEO4J] Inserting triples into Neo4j KG...")
        insert_triples_to_neo4j(triples)
        print("[NEO4J] Triples inserted successfully.")
    else:
        print("[NEO4J] No triples extracted. Skipping insertion.")

    record_file_hash(file_hash)

    return {"message": "File saved, parsed, indexed into FAISS and Neo4j KG successfully."}