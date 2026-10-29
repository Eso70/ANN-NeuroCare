# POSIX shell convenience targets. Windows: use scripts/dev.ps1 instead.
PYTHON ?= python3.11
VENV = backend/.venv/bin/python
.PHONY: install db migrate backend frontend test check
install:
	$(PYTHON) -m venv backend/.venv
	$(VENV) -m pip install -r backend/requirements.txt
	$(VENV) -m pip freeze > backend/requirements.lock.txt
	npm install --prefix frontend
db:
	docker compose up -d db
migrate:
	cd backend && .venv/bin/python -m alembic upgrade head
backend:
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1
frontend:
	npm run dev --prefix frontend
test:
	cd backend && .venv/bin/python -m pytest -q
check:
	$(VENV) -m ruff check backend
	npm run lint --prefix frontend
	npm run build --prefix frontend
