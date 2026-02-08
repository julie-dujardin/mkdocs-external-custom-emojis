# External Emojis for MkDocs

> Sync custom emojis from Slack, Discord, and more into MkDocs Material

[![CI](https://github.com/julie-dujardin/mkdocs-external-custom-emojis/workflows/CI/badge.svg)](https://github.com/julie-dujardin/mkdocs-external-custom-emojis/actions)
[![Python Version](https://img.shields.io/pypi/pyversions/mkdocs-external-custom-emojis.svg)](https://pypi.org/project/mkdocs-external-custom-emojis/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Use your organization's custom emojis directly in MkDocs with the familiar `:emoji-name:` syntax.

## Features

- 🔄 **Automatic Sync** - Emojis sync during MkDocs build
- 🔌 **Multiple Providers** - Slack, Discord, multiple workspaces
- 🔧 **Extensible** - Easy to add new providers
- 💾 **Smart Caching** - TTL-based caching minimizes API calls
- 🎯 **Filtering** - Include/exclude emoji patterns
- 🖥️ **CLI Tools** - Manage emojis from the command line
- ♿ **Accessible** - Screen reader friendly with proper alt text

## Quick Start

### 1. Install

```bash
uv add mkdocs-external-custom-emojis
# or: pip install mkdocs-external-custom-emojis
```

### 2. Configure

Create `emoji-config.toml`:

```toml
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"

[[providers]]
type = "discord"
namespace = "discord"
token_env = "DISCORD_BOT_TOKEN"
tenant_id = "DISCORD_GUILD_ID"

[[providers]]
type = "discord"
namespace = "secret_discord"
token_env = "SECOND_DISCORD_BOT_TOKEN"
tenant_id = "SECOND_DISCORD_GUILD_ID"
```

Set your token:

```bash
export SLACK_TOKEN="xoxp-your-token-here"
export DISCORD_BOT_TOKEN="MTIz..."
export DISCORD_GUILD_ID="123456789012345678"
export SECOND_DISCORD_BOT_TOKEN="MTIz..."
export SECOND_DISCORD_GUILD_ID="987654321012345678"
```

Add to `mkdocs.yml`:

```yaml
plugins:
  - external-emojis

markdown_extensions:
  - pymdownx.emoji
```

### 3. Use

```markdown
# Welcome! :partyparrot:

We love cats: :catjam: :shipit:
```

```bash
mkdocs build  # Emojis sync automatically!
```

## CLI

```bash
mkdocs-emoji init      # Create config
mkdocs-emoji sync      # Download emojis
mkdocs-emoji list      # List available emojis
mkdocs-emoji validate  # Check configuration
```

## Documentation

📚 **[Full Documentation](https://mkdocs-emoji.julie.is/)**

- [Quick Start Guide](https://mkdocs-emoji.julie.is/getting-started/quickstart/)
- [Configuration](https://mkdocs-emoji.julie.is/getting-started/configuration/)
- [CLI Commands](https://mkdocs-emoji.julie.is/user-guide/cli/)
- [Deployment](https://mkdocs-emoji.julie.is/getting-started/deployment/)

## License

MIT License - see [LICENSE](LICENSE) for details.
