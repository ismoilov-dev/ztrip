run:
	uvicorn config.asgi:application --reload & celery -A config worker --loglevel=info

run1:
	uvicorn config.asgi:application --reload

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	python manage.py shell_plus