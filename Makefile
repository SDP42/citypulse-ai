.PHONY: setup dev api web test fixtures
setup:
	cd api && python3 -m venv .venv && .venv/bin/pip install fastapi "uvicorn[standard]" pydantic pydantic-settings shapely pyproj h3 pytest httpx hypothesis python-multipart osmium
	cd web && npm install
api:
	cd api && .venv/bin/uvicorn citypulse.main:app --reload --port 8000
web:
	cd web && npm run dev
dev:
	$(MAKE) -j2 api web
test:
	cd api && .venv/bin/pytest -q
	cd web && npm test --if-present
fixtures:
	api/.venv/bin/python scripts/make_fixtures.py
