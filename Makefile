setup:
	poetry install

test:
	poetry run pytest

tox-test:
	poetry run tox

docs:
	poetry run mkdocs serve

docs-build:
	poetry run mkdocs build

clean:
	rm -rf .tox
	rm -rf site
	rm -rf dist
	rm -rf */.pytest_cache
	rm -rf */__pycache__
	rm -rf .pytest_cache
	rm -rf __pycache__

export:
	poetry export --without-hashes --without dev -f requirements.txt -o requirements.txt

publish-test:
	poetry publish --build -r test-pypi

publish:
	poetry publish --build

.PHONY: setup tests docs clean export
