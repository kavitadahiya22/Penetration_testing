# Cybrty-Pentest Test Suite Makefile

.PHONY: help up down test smoke perf reset-os wait-os check-models ci-test clean

# Default target
help:
	@echo "Cybrty-Pentest Test Suite"
	@echo ""
	@echo "Available targets:"
	@echo "  up          - Start test environment (Docker Compose)"
	@echo "  down        - Stop test environment"
	@echo "  test        - Run all tests"
	@echo "  smoke       - Run smoke tests only"
	@echo "  recon       - Run recon agent tests"
	@echo "  web         - Run web agent tests"
	@echo "  exploit     - Run exploit agent tests"
	@echo "  creds       - Run credentials agent tests"
	@echo "  lateral     - Run lateral movement tests"
	@echo "  privesc     - Run privilege escalation tests"
	@echo "  planner     - Run planner tests"
	@echo "  logging     - Run logging validation tests"
	@echo "  policy      - Run policy and safety tests"
	@echo "  negative    - Run negative/edge case tests"
	@echo "  perf        - Run performance tests"
	@echo "  reset-os    - Reset OpenSearch indices"
	@echo "  wait-os     - Wait for OpenSearch to be ready"
	@echo "  check-models- Check available models"
	@echo "  ci-test     - Run CI test suite"
	@echo "  clean       - Clean up test artifacts"

# Environment setup
up:
	@echo "Starting test environment..."
	docker-compose -f docker/docker-compose.tests.yml up -d
	@echo "Waiting for services to be ready..."
	$(MAKE) wait-os
	@echo "Test environment ready!"

down:
	@echo "Stopping test environment..."
	docker-compose -f docker/docker-compose.tests.yml down -v
	@echo "Test environment stopped."

# Test execution
test:
	@echo "Running all tests..."
	pytest -v --tb=short --maxfail=5

smoke:
	@echo "Running smoke tests..."
	pytest -v -m "smoke" --tb=short

# Agent-specific tests
recon:
	@echo "Running recon agent tests..."
	pytest -v -m "recon" --tb=short

web:
	@echo "Running web agent tests..."
	pytest -v -m "web" --tb=short

exploit:
	@echo "Running exploit agent tests..."
	pytest -v -m "exploit" --tb=short

creds:
	@echo "Running credentials agent tests..."
	pytest -v -m "creds" --tb=short

lateral:
	@echo "Running lateral movement tests..."
	pytest -v -m "lateral" --tb=short

privesc:
	@echo "Running privilege escalation tests..."
	pytest -v -m "privesc" --tb=short

# Functional tests
planner:
	@echo "Running planner tests..."
	pytest -v -m "planner" --tb=short

logging:
	@echo "Running logging validation tests..."
	pytest -v -m "logging" --tb=short

policy:
	@echo "Running policy and safety tests..."
	pytest -v -m "policy" --tb=short

negative:
	@echo "Running negative/edge case tests..."
	pytest -v -m "negative" --tb=short

# Performance testing
perf:
	@echo "Running performance tests..."
	locust -f perf/locustfile.py --headless -u $(PERF_USERS:-20) -r $(PERF_SPAWN_RATE:-5) -t $(PERF_RUN_TIME:-2m) --html perf/report.html

# Utility targets
reset-os:
	@echo "Resetting OpenSearch indices..."
	-curl -XDELETE "http://localhost:9200/cybrty-*" 2>/dev/null || true
	@echo "OpenSearch indices reset."

wait-os:
	@echo "Waiting for OpenSearch to be ready..."
	@timeout=60; \
	while [ $$timeout -gt 0 ]; do \
		if curl -s "http://localhost:9200/_cluster/health" >/dev/null 2>&1; then \
			echo "OpenSearch is ready!"; \
			break; \
		fi; \
		echo "Waiting for OpenSearch... ($$timeout seconds remaining)"; \
		sleep 2; \
		timeout=$$((timeout-2)); \
	done; \
	if [ $$timeout -le 0 ]; then \
		echo "Timeout waiting for OpenSearch"; \
		exit 1; \
	fi

check-models:
	@echo "Checking available models..."
	@if command -v curl >/dev/null 2>&1; then \
		echo "Ollama models:"; \
		curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Ollama not available"; \
	fi

# CI/CD support
ci-test:
	@echo "Running CI test suite..."
	$(MAKE) up
	$(MAKE) smoke
	$(MAKE) test
	$(MAKE) down

# Cleanup
clean:
	@echo "Cleaning up test artifacts..."
	-docker-compose -f docker/docker-compose.tests.yml down -v 2>/dev/null || true
	-rm -f perf/report.html
	-rm -rf __pycache__ .pytest_cache
	-find . -name "*.pyc" -delete
	-find . -name "*.pyo" -delete
	@echo "Cleanup complete."

# Development helpers
dev-setup:
	@echo "Setting up development environment..."
	pip install -r requirements-test.txt
	cp .env.example .env
	@echo "Development setup complete. Edit .env as needed."

logs:
	@echo "Showing service logs..."
	docker-compose -f docker/docker-compose.tests.yml logs --tail=50 -f

status:
	@echo "Service status:"
	docker-compose -f docker/docker-compose.tests.yml ps

# Quality checks
lint:
	@echo "Running code quality checks..."
	flake8 src/ e2e/ perf/ --max-line-length=120
	black --check src/ e2e/ perf/

format:
	@echo "Formatting code..."
	black src/ e2e/ perf/

# Environment variables
export PYTHONPATH := $(PWD)/src:$(PYTHONPATH)
