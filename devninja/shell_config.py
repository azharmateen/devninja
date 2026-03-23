"""Manage shell configuration (aliases, PATH, environment variables)."""

import os
import re


class ShellConfigurator:
    """Add aliases, PATH entries, and env vars to shell configuration."""

    DEVNINJA_MARKER = "# >>> devninja >>>"
    DEVNINJA_END = "# <<< devninja <<<"

    def __init__(self, system_info: dict):
        self.shell = system_info["shell"]
        self.config_file = system_info.get("shell_config", self._default_config())
        self.aliases: dict[str, str] = {}
        self.env_vars: dict[str, str] = {}
        self.path_entries: list[str] = []

    def _default_config(self) -> str:
        """Get default config file path."""
        home = os.path.expanduser("~")
        configs = {
            "zsh": os.path.join(home, ".zshrc"),
            "bash": os.path.join(home, ".bashrc"),
            "fish": os.path.join(home, ".config", "fish", "config.fish"),
        }
        return configs.get(self.shell, os.path.join(home, ".bashrc"))

    def add_alias(self, name: str, command: str):
        """Add a shell alias."""
        self.aliases[name] = command

    def add_env_var(self, name: str, value: str):
        """Add an environment variable."""
        self.env_vars[name] = value

    def add_path(self, path_entry: str):
        """Add a PATH entry."""
        # Expand ~ and env vars
        expanded = os.path.expanduser(os.path.expandvars(path_entry))
        if expanded not in self.path_entries:
            self.path_entries.append(expanded)

    def write(self):
        """Write all configuration to the shell config file."""
        if self.shell == "fish":
            block = self._generate_fish_block()
        else:
            block = self._generate_posix_block()

        self._update_config_file(block)

    def _generate_posix_block(self) -> str:
        """Generate a bash/zsh compatible configuration block."""
        lines = [self.DEVNINJA_MARKER]

        # PATH entries
        for path_entry in self.path_entries:
            lines.append(f'export PATH="{path_entry}:$PATH"')

        # Environment variables
        for name, value in self.env_vars.items():
            lines.append(f'export {name}="{value}"')

        # Aliases
        for name, command in self.aliases.items():
            lines.append(f"alias {name}='{command}'")

        lines.append(self.DEVNINJA_END)
        return "\n".join(lines)

    def _generate_fish_block(self) -> str:
        """Generate a fish shell compatible configuration block."""
        lines = [self.DEVNINJA_MARKER]

        # PATH entries
        for path_entry in self.path_entries:
            lines.append(f"fish_add_path {path_entry}")

        # Environment variables
        for name, value in self.env_vars.items():
            lines.append(f'set -gx {name} "{value}"')

        # Aliases (fish uses abbreviations or functions)
        for name, command in self.aliases.items():
            lines.append(f"abbr --add {name} '{command}'")

        lines.append(self.DEVNINJA_END)
        return "\n".join(lines)

    def _update_config_file(self, block: str):
        """Update the config file, replacing any existing devninja block."""
        content = ""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                content = f.read()

        # Remove existing devninja block
        pattern = re.escape(self.DEVNINJA_MARKER) + r".*?" + re.escape(self.DEVNINJA_END)
        content = re.sub(pattern, "", content, flags=re.DOTALL)

        # Clean up extra blank lines
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = content.rstrip()

        # Append new block
        if content:
            content += "\n\n"
        content += block + "\n"

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        with open(self.config_file, "w") as f:
            f.write(content)
