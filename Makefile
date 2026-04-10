run:
	uvicorn config.asgi:application --reload & celery -A config worker --loglevel=info

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	python manage.py shell_plus