# MicroAppFinder Worker

Background worker for processing analysis runs.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run the worker
python -m worker.main
```

## Pipeline Steps

1. **Provider Search** - Search Reddit, HN, PH, IH for URLs
2. **Fetch** - Fetch content using crawl4ai
3. **Normalize** - Convert to Signal schema
4. **Deduplicate** - Remove duplicates
5. **Cluster** - Group similar signals
6. **Score** - Calculate opportunity scores
7. **Generate Briefs** - Create micro-app briefs

## Development

The worker listens on Redis queues:
- `high` - High priority jobs
- `default` - Normal jobs
- `low` - Low priority jobs
