publish:
	poetry version patch
	VERSION=$$(awk -F '"' '/^version/ {print $$2}' pyproject.toml); git add .; git commit -m "release $$VERSION"
	poetry publish --build

test-coverage:
	poetry run pytest --cov=src/telegram_libs tests/