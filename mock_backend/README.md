# Mock Backend

Standalone mock backend for AI Interview Automation development.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - Unix: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

Run the application from the `mock_backend` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

## Structure

- `app/`: Main application package
  - `api/`: API endpoints
  - `db/`: Database configuration (placeholder)
  - `schemas/`: Pydantic models
- `requirements.txt`: Project dependencies
