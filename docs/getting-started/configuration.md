# Configuration :claudethinking:

This guide covers all configuration options for mkdocs-external-custom-emojis.

## Configuration Files

The plugin uses two configuration files:

1. **`emoji-config.toml`** - Emoji provider and cache settings
2. **`mkdocs.yml`** - MkDocs plugin configuration

## emoji-config.toml

### Complete Example

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

[providers.filters]
include_patterns = ["party*", "cat*"]
exclude_patterns = ["*-old"]
```

### Cache Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `directory` | string | `.mkdocs_emoji_cache` | Where to store downloaded emojis |
| `ttl_hours` | integer | 24 | Re-fetch after this many hours |
| `clean_on_build` | boolean | false | Clean cache before each build |

#### Examples

=== "Long TTL"

    ```toml
    [cache]
    ttl_hours = 168  # 1 week
    ```

=== "Always Fresh"

    ```toml
    [cache]
    ttl_hours = 1
    clean_on_build = true
    ```

=== "Custom Directory"

    ```toml
    [cache]
    directory = ".emoji_cache"
    ```

### Emoji Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `namespace_prefix_required` | boolean | `false` | If true, only `:<namespace>-<emoji>:` works |
| `max_size_kb` | integer | 500 | Skip emojis larger than this |

#### Namespace Prefix

By default, both syntaxes work for any emoji:

- `:partyparrot:` - short form
- `:slack-partyparrot:` - namespaced form

Set `namespace_prefix_required = true` to require the namespace prefix:

=== "Default (both work)"

    ```toml
    [emojis]
    namespace_prefix_required = false
    ```

    Usage: `:partyparrot:` or `:slack-partyparrot:`

=== "Namespace required"

    ```toml
    [emojis]
    namespace_prefix_required = true
    ```

    Usage: `:slack-partyparrot:` only

    !!! tip
        Use this when you have multiple providers with potentially conflicting emoji names.

### Provider Configuration

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `type` | string | ✓ | Provider type (`"slack"`, `"discord"`) |
| `namespace` | string | ✓ | Unique namespace for this provider |
| `token_env` | string | ✓ | Environment variable containing the API token |
| `tenant_id` | string |  | Env var for tenant/server ID (required for Discord) |
| `enabled` | boolean |  | Enable/disable this provider |

#### Slack Provider

```toml
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"
```

#### Discord Provider

```toml
[[providers]]
type = "discord"
namespace = "discord"
token_env = "DISCORD_BOT_TOKEN"
tenant_id = "DISCORD_GUILD_ID"  # Env var containing guild/server ID
```

!!! info "Discord Setup"
    - `token_env`: Env var containing the bot token
    - `tenant_id`: Env var containing the guild/server ID (right-click server → Copy Server ID with Developer Mode enabled)

#### Multiple Providers :mind_blown:

```toml
# Personal Slack
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"

# Work Slack
[[providers]]
type = "slack"
namespace = "work"
token_env = "WORK_SLACK_TOKEN"

# Temporarily disabled
[[providers]]
type = "slack"
namespace = "archive"
token_env = "ARCHIVE_SLACK_TOKEN"
enabled = false
```

### Filtering :catjam:

Filter which emojis to sync using glob patterns:

```toml
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"

[providers.filters]
include_patterns = ["party*", "cat*", "dog*"]  # Only these
exclude_patterns = ["*-old", "*-backup"]        # Skip these
```

!!! info "Pattern Matching :galaxy_brain:"
    - Uses standard glob patterns (`*`, `?`, `[abc]`)
    - `include_patterns` - whitelist (only sync matching)
    - `exclude_patterns` - blacklist (skip matching)
    - Exclude is checked first, then include

#### Filter Examples

=== "Category Filter"

    ```toml
    [providers.filters]
    include_patterns = ["party*", "celebration*", "tada*"]
    ```

=== "Exclude Old"

    ```toml
    [providers.filters]
    exclude_patterns = ["*-old", "*-deprecated", "*-backup"]
    ```

=== "Combined"

    ```toml
    [providers.filters]
    include_patterns = ["team-*", "project-*"]
    exclude_patterns = ["*-archive"]
    ```

## mkdocs.yml

### Plugin Configuration

```yaml
plugins:
  - external-emojis:
      config_file: emoji-config.toml  # default
      icons_dir: overrides/assets/emojis      # default
      enabled: true                    # default
      fail_on_error: true              # default
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `config_file` | string | `emoji-config.toml` | Path to emoji config |
| `icons_dir` | string | `overrides/assets/emojis` | Where to put synced icons |
| `enabled` | boolean | true | Enable/disable plugin |
| `fail_on_error` | boolean | true | Fail build on errors |

### Markdown Extensions

Required configuration:

```yaml
markdown_extensions:
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
```

The plugin automatically adds `overrides/assets/emojis` to `custom_icons`.

## Environment Variables

All sensitive data (tokens) should be in environment variables:

```bash
# Slack
export SLACK_TOKEN="xoxp-..."

# Discord
export DISCORD_BOT_TOKEN="MTIz..."
export DISCORD_GUILD_ID="123456789012345678"

# Multiple Slack workspaces
export SLACK_TOKEN="xoxp-personal-..."
export WORK_SLACK_TOKEN="xoxp-work-..."
```

### CI/CD

=== "GitHub Actions"

    ```yaml
    - name: Build docs
      env:
        SLACK_TOKEN: ${{ secrets.SLACK_TOKEN }}
        DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
        DISCORD_GUILD_ID: ${{ secrets.DISCORD_GUILD_ID }}
      run: mkdocs build
    ```

=== "GitLab CI"

    ```yaml
    build:
      script:
        - mkdocs build
      variables:
        SLACK_TOKEN: $SLACK_TOKEN
        DISCORD_BOT_TOKEN: $DISCORD_BOT_TOKEN
        DISCORD_GUILD_ID: $DISCORD_GUILD_ID
    ```

=== "Environment File"

    ```bash
    # .env (don't commit!)
    SLACK_TOKEN=xoxp-...
    DISCORD_BOT_TOKEN=MTIz...
    DISCORD_GUILD_ID=123456789012345678
    ```

## Next Steps

- [CLI Commands](../user-guide/cli.md) - All CLI options
- [Contributing](../development/contributing.md) - Help improve the project
