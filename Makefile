setup:
	poetry install

docker-setup:
	poetry install --no-interaction --no-ansi
	
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

django-migrate:
	poetry run python -Wd src/manage.py makemigrations
	poetry run python -Wd src/manage.py migrate

django-start-dev:
	poetry run python -Wd src/manage.py makemigrations
	poetry run python -Wd src/manage.py migrate
	poetry run python -Wd src/manage.py createsuperuser --noinput \
	 --username ${DJANGO_SUPERUSER_USERNAME} --email ${DJANGO_SUPERUSER_EMAIL}
	poetry run python -Wd src/manage.py loaddata src/umli_app/fixtures/uml_models_data.json
	poetry run python -Wd src/manage.py runserver 0.0.0.0:8000

django-start:
	poetry run python -Wd src/manage.py makemigrations
	poetry run python -Wd src/manage.py migrate
	poetry run python -Wd src/manage.py createsuperuser --noinput \
	 --username ${DJANGO_SUPERUSER_USERNAME} --email ${DJANGO_SUPERUSER_EMAIL}
	poetry run python -Wd src/manage.py runserver 0.0.0.0:8000


.PHONY: setup setup-docker tests tox-test docs clean export
