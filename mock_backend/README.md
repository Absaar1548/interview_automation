# AI Interview Automation - Mock Backend

Standalone backend for the AI Interview Automation platform, powered by FastAPI and PostgreSQL.

## 🚀 Setup & Installation

### 1️⃣ Prerequisites
- Python 3.10+
- PostgreSQL 15+
- Git

### 2️⃣ Clone & Workspace Setup

Clone the repository and spin up a new virtual Python environment:
```bash
git clone <your-repo-url>
cd mock_backend

# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Setup PostgreSQL

**1. Create the Database**
Open `psql` using `psql -U postgres` and run:
```sql
CREATE DATABASE interview_db;
\q
```

**2. Configure Environment Variables**
Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql+asyncpg://postgres:YourPassword@localhost:5432/interview_db
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```
> [!CAUTION] 
> If your database password contains an `@` symbol, you must URL-encode it as `%40`. Example: `password@123` → `password%40123`.

**3. Run Database Migrations**
Initialize the relational schema using Alembic:
```bash
alembic upgrade head
```

**4. Seed Initial Data**
Populate the database with a default Admin and Interview template:
```bash
python seed_db.py
```

## ⚡ Running the App

Start the Uvicorn development server:
```bash
uvicorn app.main:app --reload
```
- **API Server:** `http://127.0.0.1:8000`
- **Swagger Documentation:** `http://127.0.0.1:8000/docs`

## 🧪 Troubleshooting

**Error: 500 on Schedule**
- Ensure `curated_questions` is being returned in the response schema.
- Confirm all Alembic migrations are applied.
- Confirm you ran `seed_db.py`.

**Error: invalid interpolation syntax (%40)**
In `alembic/env.py`, ensure the following is configured:
```python
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("%", "%%")
)
```

## 🏗️ Project Structure

- `app/`: Main application code
  - `api/`: FastAPI route definitions
  - `core/`: Security, configurations, and core logic
  - `db/`: Database connection, models, and repositories (UnitOfWork)
  - `schemas/`: Pydantic validation models
  - `services/`: Decoupled business logic
- `alembic/`: Database migration scripts
- `tests/`: Integration and Jupyter notebook tests
- `requirements.txt`: Python package dependencies
