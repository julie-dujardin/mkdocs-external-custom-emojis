# Quick Start :fastparrot:

Get custom Slack or Discord emojis in your MkDocs site in 5 minutes!

## Step 1: Get Your Token

=== "Slack"

    1. Go to [api.slack.com/apps](https://api.slack.com/apps)
    2. Create a new app or select an existing one
    3. Add the `emoji:read` scope under **OAuth & Permissions**
    4. Install the app to your workspace
    5. Copy the **OAuth Access Token** (starts with `xoxp-`)

=== "Discord"

    1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
    2. Create a new application or select an existing one
    3. Go to **Bot** and create a bot if needed
    4. Grant `bot` → `<Manage/Create> Expressions` permissions
    5. Copy the **Bot Token**
    6. Note your **Guild/Server ID** (enable Developer Mode, right-click server)

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

```yaml
plugins:
  - search
  - external-emojis

markdown_extensions:
  - pymdownx.emoji  # The plugin auto-configures this
```

!!! tip "Plugin Order :this_is_fine:"
    Place `external-emojis` before other plugins that might use emojis.

## Step 5: Sync and Build :tada-animated:

```bash
mkdocs-emoji sync && mkdocs serve
```

You'll see:

```
Syncing slack (namespace: slack)...
✓ Synced 42, cached 0, skipped 0
```

Visit http://localhost:8000 and see your custom emojis in action!

## Step 6: Use Your Emojis :stonks:

```markdown
Check out this party parrot: :partyparrot:

Or use the namespaced version: :slack-partyparrot:
```

Both `:partyparrot:` and `:slack-partyparrot:` work by default. Set `namespace_prefix_required = true` in your config if you have multiple providers with conflicting names.

## Troubleshooting :goose_warning:

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

### Token issues? :rubberduck:

=== "Slack"

    ```bash
    curl -H "Authorization: Bearer $SLACK_TOKEN" \
      https://slack.com/api/auth.test
    ```

=== "Discord"

    ```bash
    curl -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
      "https://discord.com/api/v10/guilds/$DISCORD_GUILD_ID"
    ```

## Next Steps

- [Configuration Guide](configuration.md) - Advanced options :claudethinking:
- [CLI Commands](../user-guide/cli.md) - All CLI options :hackerman:
- [Deployment](deployment.md) - CI/CD setup :shipit:
