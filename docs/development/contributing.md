# Contributing :thankyouparrot:

Thank you for considering contributing to mkdocs-external-custom-emojis!

## Development Setup :bob_the_builder:

```bash
# Clone repository
git clone https://github.com/julie-dujardin/mkdocs-external-custom-emojis.git
cd mkdocs-external-custom-emojis

# Install with uv
uv sync --all-groups

# Install pre-commit hooks
pre-commit install
```

## Running Tests :thumbs_up:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific test
uv run pytest tests/unit/test_models.py::TestEmojiOptions
```

## Code Quality

```bash
# Run all checks
uv run pre-commit run -a
```
