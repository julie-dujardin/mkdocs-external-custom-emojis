# Deployment

This guide explains how to deploy your MkDocs documentation with external custom emojis using GitHub Actions and GitHub Pages.

## Prerequisites

Before setting up deployment, ensure you have:

1. A working MkDocs configuration with the `external-emojis` plugin
2. An `emoji-config.toml` file configured with your providers
3. A Slack token (or other provider tokens) ready to add as a secret

## GitHub Actions Setup

### Step 1: Add Your Token as a Secret

1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add your token:
    - **Name**: `SLACK_TOKEN`
    - **Value**: Your Slack token (e.g., `xoxp-...`)

!!! tip "Getting a Slack Token"
    See the [Slack documentation](https://docs.slack.dev/app-management/quickstart-app-settings) to create an app with the `emoji:read` scope.

### Step 2: Enable GitHub Pages

1. Go to **Settings** > **Pages**
2. Under **Build and deployment**, select **GitHub Actions** as the source

### Step 3: Create the Workflow

Create `.github/workflows/docs.yml` in your repository:

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

## How It Works

1. **Trigger**: The workflow runs on every push to `main` or manually via `workflow_dispatch`
2. **Build Job**:
    - Checks out your repository
    - Sets up Python and installs dependencies
    - The `SLACK_TOKEN` environment variable is pulled from GitHub secrets
    - MkDocs builds your site, and the plugin automatically syncs emojis
3. **Deploy Job**: Uploads the built site to GitHub Pages

## Multiple Providers

If you have multiple providers configured, add each token as a separate secret:

```yaml
env:
  SLACK_TOKEN: ${{ secrets.SLACK_TOKEN }}
  WORK_SLACK_TOKEN: ${{ secrets.WORK_SLACK_TOKEN }}
```

## Troubleshooting

### Build Fails with Token Error

- Verify the secret name matches `token_env` in your `emoji-config.toml`
- Check that the secret is added at the repository level, not environment level

### Emojis Not Appearing

- Ensure `fail_on_error: false` in `mkdocs.yml` if you want builds to succeed even when emoji sync fails
- Check the build logs for any provider connection errors

### Permission Denied

- Verify the workflow has the correct `permissions` block
- Ensure GitHub Pages is set to deploy from GitHub Actions
