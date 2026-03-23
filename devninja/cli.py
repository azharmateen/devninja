"""CLI entry point for devninja."""

import os
import sys

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from devninja.detector import SystemDetector
from devninja.installer import PackageInstaller
from devninja.vscode import VSCodeManager
from devninja.shell_config import ShellConfigurator
from devninja.dotfiles import DotfileManager

console = Console()
PRESETS_DIR = os.path.join(os.path.dirname(__file__), "presets")


@click.group()
@click.version_option(package_name="devninja")
def main():
    """One-command dev environment bootstrapper for any OS."""
    pass


@main.command()
@click.argument("preset")
@click.option("--dry-run", is_flag=True, help="Show what would be installed without doing it")
@click.option("--skip-vscode", is_flag=True, help="Skip VS Code extension installation")
@click.option("--skip-shell", is_flag=True, help="Skip shell configuration changes")
@click.option("--force", is_flag=True, help="Reinstall packages even if already present")
def setup(preset, dry_run, skip_vscode, skip_shell, force):
    """Set up a development environment from a preset.

    Available presets: fullstack, react, python_ml, devops, go_backend

    Example: devninja setup fullstack
    """
    preset_data = _load_preset(preset)
    if not preset_data:
        console.print(f"[red]Preset '{preset}' not found.[/]")
        console.print(f"[dim]Available: {', '.join(_list_presets())}[/]")
        sys.exit(1)

    console.print(f"[bold blue]devninja[/] setting up [cyan]{preset}[/] environment\n")

    # Detect system
    detector = SystemDetector()
    system_info = detector.detect()
    _print_system_info(system_info)

    # Show what will be installed
    packages = preset_data.get("packages", [])
    vscode_extensions = preset_data.get("vscode_extensions", [])
    shell_aliases = preset_data.get("aliases", {})
    env_vars = preset_data.get("env_vars", {})
    path_entries = preset_data.get("path_entries", [])

    if dry_run:
        _print_dry_run(packages, vscode_extensions, shell_aliases, env_vars, system_info)
        return

    # Install packages
    installer = PackageInstaller(system_info)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Installing packages...", total=len(packages))

        for pkg in packages:
            pkg_name = pkg["name"] if isinstance(pkg, dict) else pkg
            progress.update(task, description=f"Installing {pkg_name}...")

            if not force and installer.is_installed(pkg_name):
                console.print(f"  [dim]Already installed: {pkg_name}[/]")
            else:
                success, msg = installer.install(pkg)
                if success:
                    console.print(f"  [green]Installed: {pkg_name}[/]")
                else:
                    console.print(f"  [red]Failed: {pkg_name} - {msg}[/]")

            progress.advance(task)

    # VS Code extensions
    if not skip_vscode and vscode_extensions:
        console.print("\n[bold]Installing VS Code extensions...[/]")
        vscode_mgr = VSCodeManager()
        for ext in vscode_extensions:
            success, msg = vscode_mgr.install_extension(ext)
            if success:
                console.print(f"  [green]Installed: {ext}[/]")
            else:
                console.print(f"  [yellow]Skipped: {ext} - {msg}[/]")

    # Shell configuration
    if not skip_shell and (shell_aliases or env_vars or path_entries):
        console.print("\n[bold]Configuring shell...[/]")
        shell_cfg = ShellConfigurator(system_info)

        for alias_name, alias_cmd in shell_aliases.items():
            shell_cfg.add_alias(alias_name, alias_cmd)
            console.print(f"  [green]Alias: {alias_name}={alias_cmd}[/]")

        for var_name, var_value in env_vars.items():
            shell_cfg.add_env_var(var_name, var_value)
            console.print(f"  [green]Env: {var_name}={var_value}[/]")

        for path_entry in path_entries:
            shell_cfg.add_path(path_entry)
            console.print(f"  [green]PATH: {path_entry}[/]")

        shell_cfg.write()
        console.print(f"\n[dim]Shell config updated: {shell_cfg.config_file}[/]")
        console.print(f"[dim]Run: source {shell_cfg.config_file}[/]")

    console.print(f"\n[bold green]Setup complete for '{preset}' environment![/]")


@main.command("list")
def list_presets():
    """List available presets."""
    presets = _list_presets()

    table = Table(title="Available Presets")
    table.add_column("Preset", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Packages", style="green")
    table.add_column("VS Code Extensions", style="yellow")

    for name in presets:
        data = _load_preset(name)
        if data:
            desc = data.get("description", "")
            pkg_count = len(data.get("packages", []))
            ext_count = len(data.get("vscode_extensions", []))
            table.add_row(name, desc, str(pkg_count), str(ext_count))

    console.print(table)


@main.command("export")
@click.option("-o", "--output", default="devninja-export.yaml", help="Output file")
def export_config(output):
    """Export current environment configuration."""
    detector = SystemDetector()
    system_info = detector.detect()

    dotfiles = DotfileManager(system_info)
    config = dotfiles.export_config()

    with open(output, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    console.print(f"[green]Exported environment config to {output}[/]")


@main.command("import")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Show what would be applied")
def import_config(config_file, dry_run):
    """Import and apply an environment configuration."""
    with open(config_file) as f:
        config = yaml.safe_load(f)

    console.print(f"[bold blue]Importing config from {config_file}[/]\n")

    detector = SystemDetector()
    system_info = detector.detect()

    dotfiles = DotfileManager(system_info)

    if dry_run:
        console.print("[bold]Would apply:[/]")
        for section, items in config.items():
            console.print(f"  [cyan]{section}:[/] {len(items) if isinstance(items, (list, dict)) else items}")
        return

    dotfiles.import_config(config)
    console.print("[bold green]Configuration imported successfully![/]")


def _load_preset(name: str) -> dict | None:
    """Load a preset by name."""
    filepath = os.path.join(PRESETS_DIR, f"{name}.yaml")
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        return yaml.safe_load(f)


def _list_presets() -> list[str]:
    """List all available preset names."""
    if not os.path.exists(PRESETS_DIR):
        return []
    return [
        f.replace(".yaml", "")
        for f in sorted(os.listdir(PRESETS_DIR))
        if f.endswith(".yaml")
    ]


def _print_system_info(info: dict):
    """Print detected system information."""
    table = Table(title="System Detected")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("OS", info["os"])
    table.add_row("Package Manager", info["package_manager"])
    table.add_row("Shell", info["shell"])
    table.add_row("Architecture", info["arch"])
    console.print(table)
    console.print()


def _print_dry_run(packages, extensions, aliases, env_vars, system_info):
    """Print what would be installed in dry-run mode."""
    console.print("[bold yellow]DRY RUN - nothing will be installed[/]\n")

    if packages:
        console.print("[bold]Packages to install:[/]")
        installer = PackageInstaller(system_info)
        for pkg in packages:
            name = pkg["name"] if isinstance(pkg, dict) else pkg
            status = "[dim]already installed[/]" if installer.is_installed(name) else "[cyan]would install[/]"
            console.print(f"  {name} - {status}")

    if extensions:
        console.print("\n[bold]VS Code extensions:[/]")
        for ext in extensions:
            console.print(f"  {ext}")

    if aliases:
        console.print("\n[bold]Shell aliases:[/]")
        for name, cmd in aliases.items():
            console.print(f"  {name} = {cmd}")

    if env_vars:
        console.print("\n[bold]Environment variables:[/]")
        for name, val in env_vars.items():
            console.print(f"  {name} = {val}")


if __name__ == "__main__":
    main()
