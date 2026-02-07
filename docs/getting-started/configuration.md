# Configuration

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
prefix_format = "namespace-name"
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
| `prefix_format` | string | `namespace-name` | How to format emoji names |
| `max_size_kb` | integer | 500 | Skip emojis larger than this |

#### Prefix Format

Choose how emojis are named:

| Format | Example | Use Case |
|--------|---------|----------|
| `namespace-name` | `:slack-partyparrot:` | **Default** - Clear namespace separation |
| `namespace_name` | `:slack_partyparrot:` | Underscores instead of dashes |
| `name-only` | `:partyparrot:` | Single provider, shorter names |

=== "namespace-name"

    ```toml
    [emojis]
    prefix_format = "namespace-name"
    ```

    Usage: `:slack-partyparrot:`

=== "namespace_name"

    ```toml
    [emojis]
    prefix_format = "namespace_name"
    ```

    Usage: `:slack_partyparrot:`

=== "name-only"

    ```toml
    [emojis]
    prefix_format = "name-only"
    ```

    Usage: `:partyparrot:`

    !!! warning
        Careful with name-only - emoji names may conflict between providers!

### Provider Configuration

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `type` | string | ✓ | Provider type (`"slack"`) |
| `namespace` | string | ✓ | Unique namespace for this provider |
| `token_env` | string | ✓ | Environment variable name |
| `enabled` | boolean |  | Enable/disable this provider |

#### Multiple Providers

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

### Filtering

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

!!! info "Pattern Matching"
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

All sensitive data should be in environment variables:

```bash
# Required
export SLACK_TOKEN="xoxp-..."

# Multiple providers
export SLACK_TOKEN="xoxp-personal-..."
export WORK_SLACK_TOKEN="xoxp-work-..."
```

### CI/CD

=== "GitHub Actions"

    ```yaml
    - name: Build docs
      env:
        SLACK_TOKEN: ${{ secrets.SLACK_TOKEN }}
      run: mkdocs build
    ```

=== "GitLab CI"

    ```yaml
    build:
      script:
        - mkdocs build
      variables:
        SLACK_TOKEN: $SLACK_TOKEN
    ```

=== "Environment File"

    ```bash
    # .env (don't commit!)
    SLACK_TOKEN=xoxp-...
    WORK_SLACK_TOKEN=xoxp-...
    ```

## Next Steps

- [CLI Commands](../user-guide/cli.md) - All CLI options
- [Contributing](../development/contributing.md) - Help improve the project
