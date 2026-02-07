# Configuration :claudethinking:

The plugin uses two configuration files:

| File | Purpose |
|------|---------|
| `emoji-config.toml` | Providers, caching, filtering |
| `mkdocs.yml` | Plugin settings |

## Providers :shipit:

### Slack

```toml
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"
```

### Discord

```toml
[[providers]]
type = "discord"
namespace = "discord"
token_env = "DISCORD_BOT_TOKEN"
tenant_id = "DISCORD_GUILD_ID"
```

!!! info "Discord Setup"
    - `token_env`: Env var containing the bot token
    - `tenant_id`: Env var containing the guild/server ID (right-click server → Copy Server ID)

### Multiple Providers :mind_blown:

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

### Provider Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `type` | string | ✓ | `"slack"` or `"discord"` |
| `namespace` | string | ✓ | Unique namespace for this provider |
| `token_env` | string | ✓ | Env var containing the API token |
| `tenant_id` | string | | Env var for server ID (Discord only) |
| `enabled` | boolean | | Enable/disable this provider |

## Filtering :catjam:

Control which emojis to sync using glob patterns:

```toml
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"

[providers.filters]
include_patterns = ["party*", "cat*", "dog*"]
exclude_patterns = ["*-old", "*-backup"]
```

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

!!! info "Pattern Matching :galaxy_brain:"
    - Uses glob patterns (`*`, `?`, `[abc]`)
    - Exclude is checked first, then include

## Cache Settings

```toml
[cache]
directory = ".mkdocs_emoji_cache"
ttl_hours = 24
clean_on_build = false
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `directory` | string | `.mkdocs_emoji_cache` | Where to store downloaded emojis |
| `ttl_hours` | integer | 24 | Re-fetch after this many hours |
| `clean_on_build` | boolean | false | Clean cache before each build |

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

## Emoji Options

```toml
[emojis]
namespace_prefix_required = false
max_size_kb = 500
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `namespace_prefix_required` | boolean | `false` | Require `:<namespace>-<emoji>:` syntax |
| `max_size_kb` | integer | 500 | Skip emojis larger than this |

### Namespace Prefix

By default, both syntaxes work:

- `:partyparrot:` - short form
- `:slack-partyparrot:` - namespaced form

=== "Default (both work)"

    ```toml
    [emojis]
    namespace_prefix_required = false
    ```

=== "Namespace required"

    ```toml
    [emojis]
    namespace_prefix_required = true
    ```

    !!! tip
        Use this when you have multiple providers with conflicting emoji names.

## mkdocs.yml

```yaml
plugins:
  - external-emojis:
      config_file: emoji-config.toml
      icons_dir: overrides/assets/emojis
      enabled: true
      fail_on_error: true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `config_file` | string | `emoji-config.toml` | Path to emoji config |
| `icons_dir` | string | `overrides/assets/emojis` | Where to put synced icons |
| `enabled` | boolean | true | Enable/disable plugin |
| `fail_on_error` | boolean | true | Fail build on errors |

### Markdown Extensions

```yaml
markdown_extensions:
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
```

The plugin automatically adds your icons directory to `custom_icons`.

## Environment Variables :typingcat:

All tokens should be in environment variables:

```bash
export SLACK_TOKEN="xoxp-..."
export DISCORD_BOT_TOKEN="MTIz..."
export DISCORD_GUILD_ID="123456789012345678"
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
    ```

=== ".env file"

    ```bash
    # .env (don't commit!)
    SLACK_TOKEN=xoxp-...
    DISCORD_BOT_TOKEN=MTIz...
    DISCORD_GUILD_ID=123456789012345678
    ```

## Complete Example :lgtm:

```toml
[cache]
directory = ".mkdocs_emoji_cache"
ttl_hours = 24

[emojis]
namespace_prefix_required = false
max_size_kb = 500

[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"

[providers.filters]
include_patterns = ["party*", "cat*"]
exclude_patterns = ["*-old"]
```

## Next Steps

- [CLI Commands](../user-guide/cli.md) - Manage emojis :hackerman:
- [Deployment](deployment.md) - CI/CD setup :rocket_animated:
- [Contributing](../development/contributing.md) - Help improve the project :thankyouparrot:
