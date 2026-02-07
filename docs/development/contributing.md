# Contributing :thankyouparrot:

Thank you for considering contributing to mkdocs-external-custom-emojis!

## Development Setup :bob_the_builder:

```bash
git clone https://github.com/julie-dujardin/mkdocs-external-custom-emojis.git
cd mkdocs-external-custom-emojis
uv sync --all-groups
pre-commit install
```

## Running Tests :thumbs_up:

```bash
uv run pytest                # Run all tests
uv run pytest --cov          # With coverage
uv run pytest tests/unit/    # Unit tests only
uv run pytest -k "test_sync" # Specific tests
```

## Code Quality :lgtm:

```bash
uv run pre-commit run -a  # Run all checks
uv run ruff check .       # Linting
uv run ruff format .      # Formatting
```

## Project Structure :claudethinking:

```
src/mkdocs_external_custom_emojis/
├── cli.py          # CLI commands
├── config.py       # Configuration loading
├── models.py       # Data models
├── plugin.py       # MkDocs plugin
├── providers/      # Provider implementations
│   ├── base.py     # Base provider class
│   ├── slack.py    # Slack provider
│   └── discord.py  # Discord provider
└── sync.py         # Emoji sync logic
```

## Adding a New Provider :shipit:

1. Create `src/mkdocs_external_custom_emojis/providers/yourprovider.py`
2. Implement the `BaseProvider` interface
3. Register in `providers/__init__.py`
4. Add tests in `tests/unit/providers/`
5. Update documentation

```python
from .base import BaseProvider

class YourProvider(BaseProvider):
    async def fetch_emoji_list(self) -> list[Emoji]:
        ...

    async def download_emoji(self, emoji: Emoji) -> bytes:
        ...
```

## Submitting Changes :partyparrot:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `uv run pytest`
5. Run linting: `uv run pre-commit run -a`
8. Push your changes & open a Pull Request

## Code Style

- Use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Type hints are required
- Docstrings for public functions
- Tests for new functionality

## Questions? :rubberduck:

Open an issue on [GitHub](https://github.com/julie-dujardin/mkdocs-external-custom-emojis/issues)!
