# Quick Start

Get up and running with custom Slack or Discord emojis in your MkDocs site in just a few minutes!

## Step 1: Get Your Token

=== "Slack"

    1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
    2. Create a new app or select an existing one
    3. Add the `emoji:read` scope under **OAuth & Permissions**
    4. Install the app to your workspace
    5. Copy the **OAuth Access Token** (starts with `xoxp-`)

=== "Discord"

    1. Go to [https://discord.com/developers/applications](https://discord.com/developers/applications)
    2. Create a new application or select an existing one
    3. Go to **Bot** and create a bot if needed. It will need the `bot` -> `<Manage/Create> Expressions` permissions.
    4. Copy the **Bot Token**
    5. Note your **Guild/Server ID** (enable Developer Mode, right-click server)

## Step 2: Set Environment Variables

=== "Slack"

    ```bash
    # .env
    SLACK_TOKEN=xoxp-your-token-here
    ```

=== "Discord"

    ```bash
    # .env
    DISCORD_BOT_TOKEN=your-bot-token-here
    DISCORD_GUILD_ID=123456789012345678
    ```

## Step 3: Initialize Configuration

Create a default configuration file:

```bash
mkdocs-emoji init
```

This creates `emoji-config.toml`. Update it for your provider:

=== "Slack"

    ```toml
    [[providers]]
    type = "slack"
    namespace = "slack"
    token_env = "SLACK_TOKEN"
    ```

=== "Discord"

    ```toml
    [[providers]]
    type = "discord"
    namespace = "discord"
    token_env = "DISCORD_BOT_TOKEN"
    tenant_id = "DISCORD_GUILD_ID"
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

Download your emojis:

```bash
mkdocs-emoji sync
```

You'll see output like:

```
Syncing slack (namespace: slack)...
✓ Synced 42, cached 0, skipped 0

Total: 42 synced, 0 cached, 0 errors
```

## Step 6: Build Your Docs

```bash
mkdocs serve
```

Visit http://localhost:8000 and see your custom emojis in action!

## Step 7: Use your emojis :stonks:

Use emojis in your markdown with the familiar `:emoji-name:` syntax:

```markdown
Check out this party parrot: :partyparrot:

Or use the namespaced version: :slack-partyparrot:
```

By default, both the short form (`:partyparrot:`) and the namespaced form (`:slack-partyparrot:`) work. If you have multiple providers with potentially conflicting names, you can set `namespace_prefix_required = true` in your `emoji-config.toml` to require the namespace prefix.

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

=== "Slack"

    ```bash
    # Test your token
    curl -H "Authorization: Bearer $SLACK_TOKEN" \
      https://slack.com/api/auth.test
    ```

=== "Discord"

    ```bash
    # Test your token
    curl -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
      "https://discord.com/api/v10/guilds/$DISCORD_GUILD_ID"
    ```

## Next Steps

- [Configuration Guide](configuration.md) - Learn about advanced configuration
- [CLI Commands](../user-guide/cli.md) - All CLI options
