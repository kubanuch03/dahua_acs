echo "Starting entrypoint script..."

uv sync 


echo "Applying migrations..."
# uv run python manage.py collectstatic --noinput
# uv run -- python manage.py migrate

uv run -- python manage.py runserver 0.0.0.0:8000
