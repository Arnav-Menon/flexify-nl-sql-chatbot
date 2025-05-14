# app.py
import os
import re
import sqlite3
import pandas as pd
from openai import AzureOpenAI

from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from sentence_transformers import SentenceTransformer
import faiss

from config import settings

# ─── Configuration ──────────────────────────────────────────────────────────────
MOCK_DIR             = settings.MOCK_DIR
DB_PATH              = settings.DB_PATH
AZURE_OAI_ENDPOINT   = settings.AZURE_OPENAI_ENDPOINT
AZURE_OAI_KEY        = settings.AZURE_OPENAI_KEY
AZURE_OAI_DEPLOYMENT = settings.AZURE_OPENAI_DEPLOYMENT
API_KEY              = settings.CHATBOT_API_KEY

# Debug output for Azure OpenAI config
print(f"Azure OpenAI Endpoint: {AZURE_OAI_ENDPOINT}")
print(f"Azure OpenAI Deployment: {AZURE_OAI_DEPLOYMENT}")
print(f"Azure OpenAI Key: {AZURE_OAI_KEY[:4]}...{'*' * (len(AZURE_OAI_KEY) - 8)}...{AZURE_OAI_KEY[-4:]}")

# Configure AzureOpenAI client
client = AzureOpenAI(
    api_key=AZURE_OAI_KEY,
    api_version="2024-12-01-preview",
    azure_endpoint=AZURE_OAI_ENDPOINT
)

# ─── FastAPI & Auth ─────────────────────────────────────────────────────────────
app = FastAPI(title="Internal NL‑SQL Chatbot")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(key: str = Depends(api_key_header)):
    print(f"key: {key}")
    print(f"API_KEY: {API_KEY}")
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return key

# ─── Utilities ─────────────────────────────────────────────────────────────────
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [re.sub(r"\W+", "_", c.strip().lower()) for c in df.columns]
    return df

# ─── Data Ingestion & FTS5 Index ───────────────────────────────────────────────
def ingest_to_sqlite(mock_dir: str, db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # 1) Excel → tables
    for xlsx in Path(mock_dir).glob("*.xlsx"):
        sheets = pd.read_excel(xlsx, sheet_name=None)
        for name, df in sheets.items():
            df = normalize_columns(df)
            df.to_sql(name.lower(), conn, if_exists="replace", index=False)

    # 2) FAQ → table + FTS5
    faq_csv = Path(mock_dir) / "faq.csv"
    if faq_csv.exists():
        dfq = normalize_columns(pd.read_csv(faq_csv))
        dfq.to_sql("faq", conn, if_exists="replace", index=False)
        cur.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS faq_fts
            USING fts5(
              question,
              answer,
              content='faq',
              content_rowid='rowid'
            );
            INSERT INTO faq_fts(rowid, question, answer)
            SELECT rowid, question, answer FROM faq;
        """)
        print("Created FTS5 index for FAQ.")

    conn.commit()
    conn.close()

def fts_search(query: str, limit: int = 5) -> List[Dict]:
    # Clean out punctuation so FTS5 can parse it
    clean_q = re.sub(r"[^\w\s*]", " ", query)
    clean_q = re.sub(r"\s+", " ", clean_q).strip()

    print("FTS5 search:", clean_q)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cmd = (
        "SELECT question, answer, bm25(faq_fts) AS score "
        "FROM faq_fts WHERE faq_fts MATCH ? "
        "ORDER BY score LIMIT ?;"
    )
    print("Executing:", cmd, (clean_q, limit))
    cur.execute(cmd, (clean_q, limit))
    rows = cur.fetchall()
    conn.close()
    return [{"question": q, "answer": a, "score": s} for q,a,s in rows]

# ─── Semantic Fallback (Embeddings + FAISS) ────────────────────────────────────
_MODEL    = SentenceTransformer("all-MiniLM-L6-v2")
_FAISS_IDX = None
_FAQ_META  = []

def build_semantic_index():
    global _FAISS_IDX, _FAQ_META
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT rowid, question, answer FROM faq", conn)
    conn.close()
    _FAQ_META = df.to_dict(orient="records")
    embs      = _MODEL.encode(df["question"].tolist(), convert_to_numpy=True)
    idx       = faiss.IndexFlatL2(embs.shape[1])
    idx.add(embs)
    _FAISS_IDX = idx

def semantic_search(query: str, limit: int = 3) -> List[Dict]:
    emb  = _MODEL.encode([query], convert_to_numpy=True)
    dists, ids = _FAISS_IDX.search(emb, limit)
    return [
        {"question": _FAQ_META[i]["question"],
         "answer":   _FAQ_META[i]["answer"],
         "score":    float(d)}
        for (d, i) in zip(dists[0], ids[0])
    ]

# ─── NL→SQL Translation via Azure OpenAI ──────────────────────────────────────
def load_schema(db_path: str) -> str:
    conn = sqlite3.connect(db_path); cur = conn.cursor()
    lines = []
    tables = list(cur.execute("SELECT name FROM sqlite_master WHERE type='table';"))
    print("Tables found in DB:", tables)
    for (tbl,) in tables:
        cols = cur.execute(f"PRAGMA table_info({tbl});").fetchall()
        cols_def = ", ".join(f"{c[1]} {c[2]}" for c in cols)
        lines.append(f"{tbl}({cols_def})")
    conn.close()
    return "\n".join(lines)

def translate_nl_to_sql(nl: str, schema: str) -> str:
    print(f"\n=== NL->SQL Translation ===")
    print(f"Input question: {nl}")
    print(f"Schema:\n{schema}")
    
    prompt = f"""
schema:
{schema}

Convert the question into valid SQLite SQL.
Question: {nl}
SQL:"""
    print("\nSending prompt to Azure OpenAI...")
    
    resp = client.chat.completions.create(
        model=AZURE_OAI_DEPLOYMENT,
        messages=[
            {"role":"system","content":"You are a SQL generator for SQLite."},
            {"role":"user",  "content":prompt}
        ],
        max_tokens=150,
        temperature=0.0,
    )
    
    sql = resp.choices[0].message.content.strip()
    final_sql = sql.rstrip(";") + ";"
    print(f"\nGenerated SQL: {final_sql}")
    print("=== End Translation ===\n")
    
    return final_sql

# ─── Application Startup ───────────────────────────────────────────────────────
SCHEMA: str
@app.on_event("startup")
def startup_event():
    # ingest_to_sqlite(MOCK_DIR, DB_PATH)
    build_semantic_index()
    global SCHEMA
    SCHEMA = load_schema(DB_PATH)
    print("Loaded schema:\n", SCHEMA)

# ─── API Models ─────────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    source: str             # 'faq', 'semantic', or 'sql'
    data: List[Dict]
    confidence: float

# ─── Endpoints ─────────────────────────────────────────────────────────────────
@app.post("/query", response_model=QueryResponse, dependencies=[Depends(get_api_key)])
def query_bot(req: QueryRequest):
    q = req.query.strip()

    # 1) FAQ full-text (FTS5)
    faq_hits = fts_search(q)
    print("FAQ hits:", faq_hits)
    if faq_hits:
        return QueryResponse(source="faq", data=faq_hits, confidence=1.0)

    # 2) Semantic fallback
    sem_hits = semantic_search(q)
    if sem_hits:
        return QueryResponse(source="semantic", data=sem_hits, confidence=0.9)

    # 3) NL→SQL fallback
    try:
        sql = translate_nl_to_sql(q, SCHEMA)
        conn = sqlite3.connect(DB_PATH)
        df   = pd.read_sql(sql, conn)
        conn.close()
        return QueryResponse(source="sql", data=df.to_dict(orient="records"), confidence=0.7)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
