"""Manage VS Code extension installation."""

import shutil
import subprocess


class VSCodeManager:
    """Install and manage VS Code extensions."""

    def __init__(self):
        self.code_cmd = self._find_code_command()

    def _find_code_command(self) -> str | None:
        """Find the VS Code CLI command."""
        for cmd in ["code", "code-insiders", "codium"]:
            if shutil.which(cmd):
                return cmd
        return None

    def is_available(self) -> bool:
        """Check if VS Code CLI is available."""
        return self.code_cmd is not None

    def install_extension(self, extension_id: str) -> tuple[bool, str]:
        """Install a VS Code extension by ID."""
        if not self.code_cmd:
            return False, "VS Code CLI not found (install code command in PATH)"

        # Check if already installed
        if self._is_installed(extension_id):
            return True, "Already installed"

        try:
            result = subprocess.run(
                [self.code_cmd, "--install-extension", extension_id, "--force"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return True, "Installed"
            return False, result.stderr.strip()[:200]
        except subprocess.TimeoutExpired:
            return False, "Timed out"
        except FileNotFoundError:
            return False, f"Command not found: {self.code_cmd}"

    def list_installed(self) -> list[str]:
        """List installed VS Code extensions."""
        if not self.code_cmd:
            return []

        try:
            result = subprocess.run(
                [self.code_cmd, "--list-extensions"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return [ext.strip() for ext in result.stdout.split("\n") if ext.strip()]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return []

    def _is_installed(self, extension_id: str) -> bool:
        """Check if a specific extension is installed."""
        installed = self.list_installed()
        return extension_id.lower() in [e.lower() for e in installed]
