.PHONY: install sample run test

install:
	pip install -r requirements.txt

sample:
	python scripts/make_sample_data.py
	python -m src.run_pipeline --data sample

run:
	python -m src.run_pipeline --data raw

test:
	python -m pytest -q
