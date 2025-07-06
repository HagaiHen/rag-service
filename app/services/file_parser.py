import fitz  # PyMuPDF
import pandas as pd
from typing import List
from app.services.embedding import embed_text

async def parse_file(file) -> List[str]:
    content = []
    filename = file.filename
    if filename.endswith(".pdf"):
        pdf = fitz.open(stream=await file.read(), filetype="pdf")
        for page in pdf:
            content.append(page.get_text())
        pdf.close()
    elif filename.endswith(".csv"):
        df = pd.read_csv(file.file)
        content.append("\n".join(df.astype(str).agg(" ".join, axis=1)))
    elif filename.endswith(".txt"):
        file.file.seek(0)
        text = file.file.read().decode("utf-8")
        content.append(text)
    else:
        raise ValueError("Unsupported file type")

    chunks = split_text(" ".join(content))
    return chunks


def split_text(text: str, chunk_size: int = 500) -> List[str]:
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
