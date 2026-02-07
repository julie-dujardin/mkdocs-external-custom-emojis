# Quick Start

Get up and running with custom Slack emojis in your MkDocs site in just a few minutes!

## Step 1: Get a Slack Token

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Create a new app or select an existing one
3. Add the `emoji:read` scope under **OAuth & Permissions**
4. Install the app to your workspace
5. Copy the **OAuth Access Token** (starts with `xoxp-`)

## Step 2: Set Environment Variable

Add your Slack token to your environment:

```bash
# .env
SLACK_TOKEN=xoxp-your-token-here
```

## Step 3: Initialize Configuration

Create a default configuration file:

```bash
mkdocs-emoji init
```

This creates `emoji-config.toml` with sensible defaults:

```toml
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"
```

## Step 4: Add to mkdocs.yml

Add the plugin to your `mkdocs.yml`:

```yaml
plugins:
  - search
  - external-emojis  # Add this line

markdown_extensions:
  - pymdownx.emoji  # The plugin auto-configures this
```

!!! tip "Plugin Order"
    Place `external-emojis` before other plugins that might use emojis.

## Step 5: Sync Emojis

Download your Slack emojis:

```bash
mkdocs-emoji sync
```

You'll see output like:

```
Syncing slack (namespace: slack)...
✓ Synced 42, cached 0, skipped 0

Total: 42 synced, 0 cached, 0 errors
```

## Step 6: Use in Markdown

Now use your custom emojis in your documentation:

```markdown
# Welcome to Our Docs! :slack-wave:

Check out these cool features:

- :slack-rocket: Fast and easy
- :slack-sparkles: Beautiful emojis
- :slack-partyparrot: Party time!

!!! success "Success :slack-check:"
    Custom emojis work everywhere in your docs!
```

## Step 7: Build Your Docs

```bash
mkdocs serve
```

Visit http://localhost:8000 and see your custom emojis in action!

## Troubleshooting

### Emojis not showing?

1. **Check sync worked:**
   ```bash
   mkdocs-emoji list --search partyparrot
   ```

2. **Verify files exist:**
   ```bash
   ls -la .mkdocs_emoji_cache/slack/
   ls -la overrides/assets/emojis/slack/
   ```

3. **Validate configuration:**
   ```bash
   mkdocs-emoji validate --check-env --test-providers
   ```

### Token issues?

```bash
# Test your token
curl -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/auth.test
```

## Next Steps

- [Configuration Guide](configuration.md) - Learn about advanced configuration
- [CLI Commands](../user-guide/cli.md) - All CLI options
