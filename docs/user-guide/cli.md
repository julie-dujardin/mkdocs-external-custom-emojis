# CLI Commands :hackerman:

The `mkdocs-emoji` CLI manages your custom emojis.

## Quick Reference :typingcat:

| Command | Description |
|---------|-------------|
| `mkdocs-emoji init` | Create config file |
| `mkdocs-emoji sync` | Download emojis |
| `mkdocs-emoji list` | List available emojis |
| `mkdocs-emoji validate` | Check configuration |
| `mkdocs-emoji cache` | Show cache info |

## Commands

### init

Create a default configuration file.

```bash
mkdocs-emoji init                    # Creates emoji-config.toml
mkdocs-emoji init custom-config.toml # Custom path
```

### sync :partyparrot:

Download emojis from configured providers.

```bash
mkdocs-emoji sync                  # Sync all providers
mkdocs-emoji sync --force          # Force re-download
mkdocs-emoji sync --provider slack # Sync specific provider
mkdocs-emoji sync --dry-run        # Preview without syncing
```

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Config file path (default: `emoji-config.toml`) |
| `--provider` | `-p` | Only sync specific provider namespace |
| `--force` | `-f` | Force re-download even if cached |
| `--dry-run` | | Show what would be synced |

### list :catjam:

List and search available emojis.

```bash
mkdocs-emoji list                  # List all emojis
mkdocs-emoji list --search party   # Search by name
mkdocs-emoji list --format json    # JSON output
mkdocs-emoji list --provider slack # Filter by provider
```

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Config file path |
| `--provider` | `-p` | Filter by provider namespace |
| `--search` | `-s` | Search emoji names |
| `--format` | `-f` | Output format: `text` or `json` |

### validate :thonk:

Validate configuration and test connections.

```bash
mkdocs-emoji validate                   # Validate config file
mkdocs-emoji validate --check-env       # Check environment variables
mkdocs-emoji validate --test-providers  # Test provider connections
```

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Config file path |
| `--check-env` | | Verify required env vars are set |
| `--test-providers` | | Test API connections |

### cache :rubberduck:

Show cache information.

```bash
mkdocs-emoji cache                  # Show all cache info
mkdocs-emoji cache --provider slack # Specific provider
```

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Config file path |
| `--provider` | `-p` | Show info for specific provider |

## Common Workflows :stonks:

### First-time setup

```bash
mkdocs-emoji init
# Edit emoji-config.toml with your provider
mkdocs-emoji validate --check-env --test-providers
mkdocs-emoji sync
```

### Debug missing emojis

```bash
mkdocs-emoji list --search partyparrot
mkdocs-emoji cache
mkdocs-emoji sync --force
```

### Update emojis

```bash
mkdocs-emoji sync --force  # Re-download all
```
