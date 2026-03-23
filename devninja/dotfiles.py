"""Export and import dotfiles and tool configurations."""

import os
import shutil
import subprocess

import yaml


class DotfileManager:
    """Manage export and import of development environment configuration."""

    TRACKED_DOTFILES = [
        ".zshrc",
        ".bashrc",
        ".bash_profile",
        ".gitconfig",
        ".npmrc",
        ".editorconfig",
        ".vimrc",
        ".tmux.conf",
    ]

    TRACKED_CONFIG_DIRS = [
        ".config/git",
        ".config/fish",
        ".ssh/config",
    ]

    def __init__(self, system_info: dict):
        self.system_info = system_info
        self.home = system_info.get("home", os.path.expanduser("~"))

    def export_config(self) -> dict:
        """Export current environment configuration to a dict."""
        config = {
            "system": {
                "os": self.system_info["os"],
                "package_manager": self.system_info["package_manager"],
                "shell": self.system_info["shell"],
                "arch": self.system_info["arch"],
            },
            "installed_tools": self.system_info.get("installed_tools", {}),
            "dotfiles": self._export_dotfiles(),
            "vscode_extensions": self._export_vscode_extensions(),
            "shell_aliases": self._extract_aliases(),
            "env_vars": self._extract_env_vars(),
        }

        return config

    def import_config(self, config: dict):
        """Import and apply a configuration."""
        # Restore dotfiles
        dotfiles = config.get("dotfiles", {})
        for filename, content in dotfiles.items():
            filepath = os.path.join(self.home, filename)
            backup = filepath + ".devninja-backup"

            # Backup existing
            if os.path.exists(filepath) and not os.path.exists(backup):
                shutil.copy2(filepath, backup)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(content)

        # Install VS Code extensions
        extensions = config.get("vscode_extensions", [])
        if extensions and shutil.which("code"):
            for ext in extensions:
                try:
                    subprocess.run(
                        ["code", "--install-extension", ext, "--force"],
                        capture_output=True,
                        timeout=60,
                    )
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

    def _export_dotfiles(self) -> dict[str, str]:
        """Read and export tracked dotfiles."""
        dotfiles = {}

        for filename in self.TRACKED_DOTFILES:
            filepath = os.path.join(self.home, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r") as f:
                        content = f.read()
                    # Skip if too large (>100KB)
                    if len(content) < 100_000:
                        dotfiles[filename] = content
                except (IOError, UnicodeDecodeError):
                    pass

        return dotfiles

    def _export_vscode_extensions(self) -> list[str]:
        """Get list of installed VS Code extensions."""
        if not shutil.which("code"):
            return []

        try:
            result = subprocess.run(
                ["code", "--list-extensions"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return [e.strip() for e in result.stdout.split("\n") if e.strip()]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return []

    def _extract_aliases(self) -> dict[str, str]:
        """Extract shell aliases from the current shell config."""
        aliases = {}
        config_file = self.system_info.get("shell_config", "")

        if not config_file or not os.path.exists(config_file):
            return aliases

        try:
            with open(config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("alias ") and "=" in line:
                        # alias name='command'
                        rest = line[6:]  # remove "alias "
                        eq_idx = rest.index("=")
                        name = rest[:eq_idx]
                        value = rest[eq_idx + 1:].strip("'\"")
                        aliases[name] = value
        except (IOError, UnicodeDecodeError):
            pass

        return aliases

    def _extract_env_vars(self) -> dict[str, str]:
        """Extract exported environment variables from shell config."""
        env_vars = {}
        config_file = self.system_info.get("shell_config", "")

        if not config_file or not os.path.exists(config_file):
            return env_vars

        try:
            with open(config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("export ") and "=" in line:
                        rest = line[7:]  # remove "export "
                        eq_idx = rest.index("=")
                        name = rest[:eq_idx]
                        value = rest[eq_idx + 1:].strip("'\"")
                        # Skip PATH and common system vars
                        if name not in ("PATH", "HOME", "USER", "SHELL", "TERM"):
                            env_vars[name] = value
        except (IOError, UnicodeDecodeError):
            pass

        return env_vars
