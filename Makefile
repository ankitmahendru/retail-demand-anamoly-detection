.PHONY: install test run clean docker-build docker-run

install:
	pip install -r requirements.txt

# Run tests using pytest module
test:
	python -m pytest tests/ -v

# Run the app as a module to resolve imports correctly
run:
	python -m src.app

docker-build:
	docker build -t retail-ml-system .

docker-run:
	docker-compose up -d --build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf data/*.db models/*.pkl logs/*.log