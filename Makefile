# Mithi Baby Project Makefile

.PHONY: install start clean build

install:
	pip install -r backend/requirements.txt

start:
	@echo "Starting backend server..."
	python3 backend/server.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".venv" -exec rm -rf {} +
	find . -type d -name "venv" -exec rm -rf {} +
	find . -type f -name ".DS_Store" -delete
	rm -rf backend/venv
	rm -rf .pytest_cache

build:
	@echo "Static frontend, no build required yet."
