import os
import re
import sqlite3
import pandas as pd
from pathlib import Path

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names to snake_case."""
    df = df.copy()
    df.columns = [
        re.sub(r"\W+", "_", col.strip().lower())
        for col in df.columns
    ]
    return df

def ingest_to_sqlite(mock_dir: str, db_path: str):
    """
    1. Reads all .xlsx in mock_dir → SQLite tables.
    2. Reads faq.csv         → 'faq' table.
    3. Builds a full‑text index 'faq_fts' using SQLite FTS5.
    4. Exports JSON of each table for optional flat‑file retrieval.
    """
    mock_path = Path(mock_dir)
    os.makedirs(Path(db_path).parent, exist_ok=True)

    # Remove any old DB and connect
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1) Ingest Excel sheets
    for xlsx in mock_path.glob("*.xlsx"):
        sheets = pd.read_excel(xlsx, sheet_name=None)
        for sheet_name, df in sheets.items():
            df = normalize_columns(df)
            table_name = sheet_name.strip().lower()
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            # Export JSON
            df.to_json(mock_path / f"{table_name}.jsonl", orient="records", lines=True)

    # 2) Ingest FAQ pairs
    faq_path = mock_path / "faq.csv"
    if faq_path.exists():
        df_faq = pd.read_csv(faq_path)
        df_faq = normalize_columns(df_faq)
        df_faq.to_sql("faq", conn, if_exists="replace", index=False)
        df_faq.to_json(mock_path / "faq.jsonl", orient="records", lines=True)

        # 3) Create & populate FTS5 index
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS faq_fts
            USING fts5(
                question, 
                answer, 
                content='faq', 
                content_rowid='rowid'
            );
        """)
        cursor.execute("""
            INSERT INTO faq_fts(rowid, question, answer)
            SELECT rowid, question, answer FROM faq;
        """)
        conn.commit()

    conn.close()
    print(f"Ingested data + built FAQ FTS index at {db_path}")

def sample_search(query):
    conn = sqlite3.connect('/Users/arnavmenon/Code/extra/flexify/data/app.db')
    cur  = conn.cursor()
    cur.execute("""
        SELECT question, answer, bm25(faq_fts) AS score
        FROM faq_fts
        WHERE faq_fts MATCH ?
        ORDER BY score
        LIMIT 5;
    """, (query,))
    for q, a, s in cur.fetchall():
        print(f"{s:.2f} │ Q: {q}\n     A: {a}\n")
    conn.close()

# Example usage
if __name__ == "__main__":
    MOCK_DIR = "/Users/arnavmenon/Code/extra/flexify/mock_sharepoint"
    DB_PATH  = "/Users/arnavmenon/Code/extra/flexify/data/app.db"
    # ingest_to_sqlite(MOCK_DIR, DB_PATH)
    sample_search("What is the average unit price for Electrical parts")

