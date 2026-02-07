# Deployment :shipit: :rocket_animated:

Deploy your MkDocs site with custom emojis using GitHub Actions.

## Prerequisites

- Working MkDocs config with `external-emojis` plugin
- `emoji-config.toml` configured with your providers
- Provider tokens ready to add as secrets

## GitHub Actions Setup

### Step 1: Add Secrets

1. Go to your repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add your tokens:

| Name | Value |
|------|-------|
| `SLACK_TOKEN` | `xoxp-...` |
| `DISCORD_BOT_TOKEN` | `MTIz...` |
| `DISCORD_GUILD_ID` | `123456789...` |

### Step 2: Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Set source to **GitHub Actions**

### Step 3: Create Workflow

Create `.github/workflows/docs.yml`:

```yaml
name: Deploy Docs

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      SLACK_TOKEN: ${{ secrets.SLACK_TOKEN }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install mkdocs-material mkdocs-external-custom-emojis

      - name: Build docs
        run: mkdocs build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## How It Works :catjam:

1. **Trigger** - Runs on push to `main` or manual dispatch
2. **Build** - Installs deps, syncs emojis, builds site
3. **Deploy** - Uploads to GitHub Pages

## Multiple Providers :mind_blown:

Add each token as a separate secret:

```yaml
env:
  SLACK_TOKEN: ${{ secrets.SLACK_TOKEN }}
  DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
  DISCORD_GUILD_ID: ${{ secrets.DISCORD_GUILD_ID }}
```

## Troubleshooting :goose_warning:

### Build Fails with Token Error :facepalm2:

- Secret name must match `token_env` in `emoji-config.toml`
- Add secrets at repository level, not environment level

### Emojis Not Appearing :confused_dog:

- Set `fail_on_error: false` in `mkdocs.yml` to allow builds even if sync fails
- Check build logs for provider connection errors

### Permission Denied

- Verify the `permissions` block in workflow
- Ensure Pages source is set to GitHub Actions

## Next Steps

- [Configuration](configuration.md) - Advanced options :claudethinking:
- [CLI Commands](../user-guide/cli.md) - Debug locally :hackerman:
