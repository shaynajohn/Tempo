.PHONY: db backend frontend install sample

db:
	docker compose up -d

install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

migrate:
	cd backend && . .venv/bin/activate && alembic upgrade head

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

sample:
	curl -X POST http://localhost:8000/api/v1/ingest/upload \
		-F "file=@sample-data/garmin_activities_sample.json"
