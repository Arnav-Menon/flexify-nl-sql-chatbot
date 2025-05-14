# Flexify

A data processing and search application for manufacturing/supply chain data with integrated FAQ and natural language chatbot functionality. This system efficiently processes Excel and CSV data, provides full-text and semantic search capabilities, and offers flexible data access methods via a secure FastAPI backend.

## Features

- **Data Ingestion**: Process Excel files and CSV data into a structured SQLite database
- **Full-Text Search**: FAQ search using SQLite's FTS5
- **Semantic Search**: Uses sentence-transformers and FAISS for semantic fallback
- **Natural Language to SQL**: Uses Azure OpenAI to translate natural language to SQL queries
- **REST API**: FastAPI backend with secure API key authentication
- **Data Export**: JSON export capabilities for flexible data access
- **Column Normalization**: Automatic conversion of column names to snake_case
- **Multi-Format Support**: Handles Excel (.xlsx) and CSV files

## Prerequisites

- Python 3.x
- pip (Python package manager)
- Azure OpenAI resource (with deployment)

## Installation

1. Clone the repository:

```bash
git clone [your-repository-url]
cd flexify
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the example environment file and fill in your values:

```bash
cp example.env .env
# Edit .env with your editor and set your Azure OpenAI and API key values
```

## Environment Variables

Set these in your `.env` file (see `example.env`):

```
MOCK_DIR=./mock_sharepoint
DB_PATH=./data/app.db
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
CHATBOT_API_KEY=your-secret-key-here
```

## Project Structure

```
flexify/
├── data/                       # Database and processed data
├── mock_sharepoint/            # Sample data files
│   ├── faq.csv                 # FAQ data
│   ├── parts_list.xlsx         # Parts data
│   ├── suppliers.xlsx          # Supplier information
│   └── purchase_orders.xlsx    # Order data
├── src/
│   ├── ingest_data.py          # Data ingestion and processing
│   ├── read_data.py            # Data reading utilities
│   └── api/
│       ├── main.py             # FastAPI backend
│       └── config.py           # Settings loader
├── requirements.txt
├── example.env
└── README.md
```

## Usage

### Data Ingestion

To process your data files and create the SQLite database:

```python
from src.ingest_data import ingest_to_sqlite

MOCK_DIR = "path/to/your/data"
DB_PATH = "path/to/output/database.db"
ingest_to_sqlite(MOCK_DIR, DB_PATH)
```

### Running the API Server

Start the FastAPI server (from the project root):

```bash
uvicorn src.api.main:app --reload
```

### API Authentication

All endpoints require an API key, which you set in your `.env` as `CHATBOT_API_KEY`.  
Pass it as a header: `X-API-Key: your-secret-key-here`

### Example API Usage

```bash
curl -H "X-API-Key: your-secret-key-here" \
     -H "Content-Type: application/json" \
     -d '{"query":"What is the average unit price for Electrical parts?"}' \
     http://localhost:8000/query
```

### Endpoints

- `POST /query` — Accepts a JSON body with a `query` field. Returns the best answer from FAQ, semantic, or SQL.
- `GET /health` — Health check endpoint.

## Security Notes

- The API is protected by an API key. Do not share your key publicly.
- For production, restrict access to the API server (e.g., run inside a VNet or behind a firewall).
- Your Azure OpenAI resource should also be firewalled to only allow trusted IPs or subnets.

## Dependencies

See `requirements.txt` for all dependencies, including:
- fastapi, uvicorn
- pandas, openpyxl
- sentence-transformers, faiss-cpu
- openai
- pydantic_settings

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions and support, please open an issue in the repository.
