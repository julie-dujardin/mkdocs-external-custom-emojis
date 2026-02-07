# MkDocs External Custom Emojis

> Sync custom emojis from external providers (Slack, Discord, etc.) into MkDocs Material

[![CI](https://github.com/julie-dujardin/mkdocs-external-custom-emojis/workflows/CI/badge.svg)](https://github.com/julie-dujardin/mkdocs-external-custom-emojis/actions)
[![Python Version](https://img.shields.io/pypi/pyversions/mkdocs-external-custom-emojis.svg)](https://pypi.org/project/mkdocs-external-custom-emojis/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Use your organization's custom Slack or Discord emojis directly in MkDocs documentation with the familiar `:emoji-name:` syntax.

## Features

- 🎯 **Automatic Sync** - Emojis sync automatically during MkDocs build
- 🔒 **Secure** - Tokens stored in environment variables, never in config files
- 💾 **Smart Caching** - TTL-based caching to minimize API calls
- 🔧 **Extensible** - Easy to add new providers (Teams, etc.)
- 🎨 **Multiple Providers** - Support multiple Slack or Discord workspaces
- 🔍 **Filtering** - Include/exclude emoji patterns
- 📦 **CLI Tools** - Manage emojis with built-in CLI commands

## Quick Start

### Installation

```bash
pip install mkdocs-external-custom-emojis
```

### Configuration

1. Create `emoji-config.toml` in your project root:

```toml
# For Slack
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"

# For Discord
[[providers]]
type = "discord"
namespace = "discord"
token_env = "DISCORD_BOT_TOKEN"
tenant_id = "DISCORD_GUILD_ID"
```

2. Set your provider tokens:

```bash
# Slack
export SLACK_TOKEN="xoxp-your-token-here"

# Discord
export DISCORD_BOT_TOKEN="your-bot-token-here"
export DISCORD_GUILD_ID="123456789012345678"
```

> Get a Slack token: https://docs.slack.dev/app-management/quickstart-app-settings (requires `emoji:read` scope)
> Get a Discord token: https://discord.com/developers/applications (requires bot with server access)

3. Add the plugin to `mkdocs.yml`:

```yaml
plugins:
  - external-emojis

markdown_extensions:
  - pymdownx.emoji  # The plugin auto-configures this
```

### Usage

Use emojis in your markdown:

```markdown
# Welcome to our docs! :slack-wave:

Check out our party parrot: :slack-partyparrot:

We love cats: :slack-catjam: :slack-catdance:
```

Build your docs:

```bash
mkdocs build  # Emojis sync automatically!
```

## Configuration

### Full Configuration Example

```toml
# Cache configuration
[cache]
directory = ".mkdocs_emoji_cache"
ttl_hours = 24
clean_on_build = false

# Global emoji options
[emojis]
namespace_prefix_required = false
max_size_kb = 500

# Slack provider
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"
enabled = true

# Discord provider
[[providers]]
type = "discord"
namespace = "discord"
token_env = "DISCORD_BOT_TOKEN"
tenant_id = "DISCORD_GUILD_ID"
enabled = true

# Optional: Filter emojis
[providers.filters]
include_patterns = ["party*", "cat*"]
exclude_patterns = ["*-old"]

# Multiple workspaces
[[providers]]
type = "slack"
namespace = "work"
token_env = "WORK_SLACK_TOKEN"
```

### Plugin Options

Configure in `mkdocs.yml`:

```yaml
plugins:
  - external-emojis:
      config_file: emoji-config.toml  # default
      icons_dir: overrides/assets/emojis     # default
      enabled: true                   # default
      fail_on_error: true             # default
```

## CLI Commands

The plugin includes a CLI for managing emojis outside of the build process:

```bash
mkdocs-emoji init      # Initialize configuration
mkdocs-emoji sync      # Sync emojis from providers
mkdocs-emoji list      # List available emojis
mkdocs-emoji validate  # Validate configuration
mkdocs-emoji cache     # Show cache info
```

See the [CLI documentation](https://julie-dujardin.github.io/mkdocs-external-custom-emojis/user-guide/cli/) for all options.

## How It Works

1. **Build Start** - MkDocs plugin activates
2. **Fetch Emoji List** - Provider API called (cached if fresh)
3. **Download Emojis** - Missing/stale emojis downloaded
4. **Sync to Icons Dir** - Emojis placed in `overrides/assets/emojis/<namespace>/`
5. **MkDocs Renders** - Material theme finds custom icons automatically

## CI/CD Integration

Add your provider tokens as GitHub secrets (e.g., `SLACK_TOKEN`, `DISCORD_BOT_TOKEN`), then use them in your workflow:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      SLACK_TOKEN: ${{ secrets.SLACK_TOKEN }}
      DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
      DISCORD_GUILD_ID: ${{ secrets.DISCORD_GUILD_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install mkdocs-material mkdocs-external-custom-emojis
      - run: mkdocs build
```

See the [Deployment Guide](https://julie-dujardin.github.io/mkdocs-external-custom-emojis/getting-started/deployment/) for complete GitHub Pages setup instructions.
