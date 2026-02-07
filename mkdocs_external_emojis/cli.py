"""Command-line interface for emoji management."""

import json
import sys

import click

from mkdocs_external_emojis import __version__
from mkdocs_external_emojis.config import (
    ConfigError,
    create_default_config,
    load_config,
    validate_environment,
)
from mkdocs_external_emojis.models import ProviderType
from mkdocs_external_emojis.providers import ProviderError, SlackEmojiProvider
from mkdocs_external_emojis.sync import EmojiCache, SyncManager


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Manage custom emojis for MkDocs."""
    pass


@main.command()
@click.option(
    "--config",
    "-c",
    default="emoji-config.toml",
    help="Path to emoji configuration file",
)
@click.option(
    "--provider",
    "-p",
    help="Only sync specific provider namespace",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force re-download even if cached",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be synced without actually syncing",
)
def sync(config: str, provider: str | None, force: bool, dry_run: bool) -> None:
    """Sync emojis from configured providers."""
    try:
        emoji_config = load_config(config)
    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Validate environment
    missing = validate_environment(emoji_config)
    if missing:
        click.echo(
            f"Error: Missing environment variables: {', '.join(missing)}",
            err=True,
        )
        sys.exit(1)

    # Initialize sync manager
    sync_manager = SyncManager(
        cache_config=emoji_config.cache,
        emoji_options=emoji_config.emojis,
    )

    # Filter providers if specific one requested
    providers_to_sync = emoji_config.get_enabled_providers()
    if provider:
        providers_to_sync = [p for p in providers_to_sync if p.namespace == provider]
        if not providers_to_sync:
            click.echo(f"Error: Provider '{provider}' not found", err=True)
            sys.exit(1)

    # Sync each provider
    total_synced = 0
    total_cached = 0
    total_errors = 0

    for provider_config in providers_to_sync:
        click.echo(
            f"Syncing {provider_config.type.value} (namespace: {provider_config.namespace})..."
        )

        if dry_run:
            click.echo("  [DRY RUN] Would sync emojis")
            continue

        # Create provider
        try:
            if provider_config.type == ProviderType.SLACK:
                provider_instance = SlackEmojiProvider(provider_config)
            else:
                click.echo(
                    f"  Error: Unsupported provider type: {provider_config.type}",
                    err=True,
                )
                continue
        except ProviderError as e:
            click.echo(f"  Error: {e}", err=True)
            total_errors += 1
            continue

        # Sync
        with click.progressbar(
            length=100,
            label=f"  {provider_config.namespace}",
        ) as bar:

            def progress(name: str, current: int, total: int) -> None:
                bar.update((current * 100) // total - bar.pos)

            result = sync_manager.sync_provider(
                provider_instance,
                force=force,
                progress_callback=progress,
            )

        click.echo(f"  ✓ Synced {result.synced}, cached {result.cached}, skipped {result.skipped}")

        total_synced += result.synced
        total_cached += result.cached
        total_errors += len(result.errors)

        if result.errors:
            click.echo(f"  ⚠ {len(result.errors)} errors occurred")

    click.echo(f"\nTotal: {total_synced} synced, {total_cached} cached, {total_errors} errors")


@main.command()
@click.option(
    "--config",
    "-c",
    default="emoji-config.toml",
    help="Path to emoji configuration file",
)
@click.option(
    "--provider",
    "-p",
    help="Filter by provider namespace",
)
@click.option(
    "--search",
    "-s",
    help="Search emoji names",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def list(config: str, provider: str | None, search: str | None, format: str) -> None:
    """List available emojis."""
    try:
        emoji_config = load_config(config)
    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Validate environment
    missing = validate_environment(emoji_config)
    if missing:
        click.echo(
            f"Error: Missing environment variables: {', '.join(missing)}",
            err=True,
        )
        sys.exit(1)

    # Fetch emojis from providers
    all_emojis: dict[str, dict[str, str]] = {}

    providers_to_list = emoji_config.get_enabled_providers()
    if provider:
        providers_to_list = [p for p in providers_to_list if p.namespace == provider]

    for provider_config in providers_to_list:
        # Create provider
        try:
            if provider_config.type == ProviderType.SLACK:
                provider_instance = SlackEmojiProvider(provider_config)
            else:
                continue
        except ProviderError as e:
            click.echo(f"Error: {e}", err=True)
            continue

        # Fetch emojis
        try:
            emojis = provider_instance.fetch_emojis()
            namespace_emojis: dict[str, str] = {}

            for name, info in emojis.items():
                # Apply search filter
                if search and search.lower() not in name.lower():
                    continue

                emoji_name = emoji_config.emojis.format_emoji_name(provider_config.namespace, name)
                namespace_emojis[emoji_name] = info.url or ""

            all_emojis[provider_config.namespace] = namespace_emojis

        except ProviderError as e:
            click.echo(f"Error fetching from {provider_config.namespace}: {e}", err=True)

    # Output
    if format == "json":
        click.echo(json.dumps(all_emojis, indent=2))
    else:
        for namespace, emoji_dict in all_emojis.items():
            click.echo(f"\n{namespace} ({len(emoji_dict)} emojis):")
            for name in sorted(emoji_dict.keys())[:50]:  # Show first 50
                click.echo(f"  :{name}:")
            if len(emoji_dict) > 50:
                click.echo(f"  ... and {len(emoji_dict) - 50} more")


@main.command()
@click.option(
    "--config",
    "-c",
    default="emoji-config.toml",
    help="Path to emoji configuration file",
)
@click.option(
    "--check-env",
    is_flag=True,
    help="Check environment variables",
)
@click.option(
    "--test-providers",
    is_flag=True,
    help="Test provider connections",
)
def validate(config: str, check_env: bool, test_providers: bool) -> None:
    """Validate emoji configuration."""
    # Load config
    try:
        emoji_config = load_config(config)
        click.echo(f"✓ Configuration file is valid: {config}")
    except ConfigError as e:
        click.echo(f"✗ Configuration error: {e}", err=True)
        sys.exit(1)

    # Check providers
    providers = emoji_config.get_enabled_providers()
    click.echo(f"✓ Found {len(providers)} enabled provider(s)")

    for p in providers:
        click.echo(f"  - {p.type.value} (namespace: {p.namespace})")

    # Check environment variables
    if check_env:
        click.echo("\nChecking environment variables...")
        missing = validate_environment(emoji_config)

        if missing:
            click.echo(f"✗ Missing variables: {', '.join(missing)}", err=True)
            sys.exit(1)
        else:
            click.echo("✓ All required environment variables are set")

    # Test providers
    if test_providers:
        click.echo("\nTesting provider connections...")

        for provider_config in providers:
            try:
                if provider_config.type == ProviderType.SLACK:
                    provider_instance = SlackEmojiProvider(provider_config)
                    emoji_count = provider_instance.validate_config()
                    click.echo(f"✓ {provider_config.namespace}: Connection successful - found {emoji_count} emojis")
                else:
                    click.echo(f"⚠ {provider_config.namespace}: Unsupported type")
            except ProviderError as e:
                click.echo(f"✗ {provider_config.namespace}: {e}", err=True)

    click.echo("\n✓ Validation complete")


@main.command()
@click.option(
    "--config",
    "-c",
    default="emoji-config.toml",
    help="Path to emoji configuration file",
)
@click.option(
    "--provider",
    "-p",
    help="Show info for specific provider",
)
def cache(config: str, provider: str | None) -> None:
    """Show cache information."""
    try:
        emoji_config = load_config(config)
    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    providers_to_check = emoji_config.get_enabled_providers()
    if provider:
        providers_to_check = [p for p in providers_to_check if p.namespace == provider]

    for provider_config in providers_to_check:
        cache_instance = EmojiCache(emoji_config.cache, provider_config.namespace)
        stats = cache_instance.get_stats()

        click.echo(f"\n{provider_config.namespace}:")
        click.echo(f"  Files: {stats['total_files']}")
        click.echo(f"  Size: {stats['total_size_mb']} MB")
        click.echo(f"  Location: {stats['cache_dir']}")


@main.command()
@click.argument("path", default="emoji-config.toml")
def init(path: str) -> None:
    """Create a default configuration file."""
    try:
        create_default_config(path)
        click.echo(f"✓ Created configuration file: {path}")
        click.echo("\nNext steps:")
        click.echo("1. Edit the configuration file to add your provider tokens")
        click.echo("2. Set environment variables (e.g., export SLACK_TOKEN=...)")
        click.echo("3. Run: mkdocs-emoji sync")
    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
