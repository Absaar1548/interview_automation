from fastapi.testclient import TestClient
from app.main import app
import uuid
import datetime

client = TestClient(app)

print("Starting diagnosis...")

req = {"username": "admin", "password": "admin123"}
resp = client.post("/api/v1/auth/login/admin", json=req)
t = resp.json().get("access_token")

c_req = {"candidate_name": "Test", "candidate_email": f"diag{uuid.uuid4().hex[:6]}@example.com", "job_description": "dev"}
files = {"resume": ("resume.pdf", b"pdf mock", "application/pdf")}
resp_c = client.post("/api/v1/auth/admin/register-candidate", data=c_req, files=files, headers={"Authorization": f"Bearer {t}"})

# Seed template
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import asyncio

async def seed_template():
    template_id = str(uuid.uuid4())
    engine = create_async_engine("postgresql+asyncpg://postgres:Password%401548@localhost:5432/interview_db")
    async with engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO interview_templates (id, title, description, is_active, settings) VALUES (:id, 'Test', 'T', true, '{}') ON CONFLICT DO NOTHING"),
            {"id": template_id}
        )
    return template_id

template_id = asyncio.run(seed_template())

print(f"Cand ID: {resp_c.json()['id']}, Temp ID: {template_id}")

try:
    resp_s = client.post(
        "/api/v1/admin/interviews/schedule",
        json={
            "template_id": template_id,
            "candidate_id": resp_c.json()["id"],
            "scheduled_at": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).isoformat()
        },
        headers={"Authorization": f"Bearer {t}"}
    )
    print("Schedule Code:", resp_s.status_code)
    print("Schedule Body:", resp_s.text)
except Exception as e:
    import traceback
    traceback.print_exc()

