.PHONY: install test coverage lint format typecheck check run run-prod docker-build docker-run docker-compose-up docker-compose-down k8s-deploy k8s-delete clean

install:
	pip install -e ".[dev]"

test:
	pytest

coverage:
	pytest --cov=analyzer --cov=tantra --cov-report=term-missing --cov-fail-under=90

lint:
	ruff check analyzer tantra tests api.py

format:
	ruff format analyzer tantra tests api.py

typecheck:
	mypy analyzer

check: lint typecheck coverage

run:
	python api.py

run-prod:
	gunicorn "api:app" --workers 4 --bind 0.0.0.0:5000 --timeout 30 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile - --log-level info

# Docker commands
docker-build:
	docker build -t keshav:latest .

docker-run:
	docker run -d --name keshav-api -p 5000:5000 --restart unless-stopped keshav:latest

docker-stop:
	docker stop keshav-api && docker rm keshav-api

docker-logs:
	docker logs -f keshav-api

# Docker Compose commands
docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-compose-logs:
	docker-compose logs -f keshav

# Kubernetes commands
k8s-deploy:
	kubectl apply -f k8s-deployment.yaml

k8s-delete:
	kubectl delete -f k8s-deployment.yaml

k8s-status:
	kubectl get pods -n keshav

k8s-logs:
	kubectl logs -n keshav -l app=keshav --tail=100 -f

# Cleanup
clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache','.coverage','htmlcov','.mypy_cache','.ruff_cache']]"
