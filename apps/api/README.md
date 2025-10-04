# MicroAppFinder API

FastAPI backend for MicroAppFinder.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Run the server
uvicorn app.main:app --reload
```

## Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── core/                # Core configuration
│   ├── config.py       # Settings
│   └── database.py     # Database connection
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── routers/            # API routes
├── providers/          # Data providers (Reddit, HN, etc.)
└── services/           # Business logic
```

## API Endpoints

- `POST /api/runs` - Create new analysis run
- `GET /api/runs/{id}` - Get run status
- `GET /api/runs/{id}/report` - Get full report
- `POST /api/exports/{id}` - Export report

## Development

- Run tests: `pytest`
- Format code: `black .`
- Type check: `mypy .`
