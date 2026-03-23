"""Install packages via the detected package manager."""

import shutil
import subprocess
from typing import Any


class PackageInstaller:
    """Install packages using the system's package manager."""

    # Map generic package names to package-manager-specific names
    PACKAGE_ALIASES = {
        "brew": {
            "python": "python@3",
            "node": "node",
            "docker": "docker",
            "postgresql": "postgresql@16",
            "redis": "redis",
            "go": "go",
            "kubectl": "kubectl",
            "helm": "helm",
            "terraform": "terraform",
            "awscli": "awscli",
            "conda": "miniconda",
        },
        "apt": {
            "python": "python3",
            "node": "nodejs",
            "docker": "docker.io",
            "postgresql": "postgresql",
            "redis": "redis-server",
            "go": "golang",
            "kubectl": "kubectl",
            "helm": "helm",
            "terraform": "terraform",
            "awscli": "awscli",
            "conda": "conda",
        },
        "dnf": {
            "python": "python3",
            "node": "nodejs",
            "docker": "docker",
            "postgresql": "postgresql-server",
            "redis": "redis",
            "go": "golang",
        },
        "yum": {
            "python": "python3",
            "node": "nodejs",
            "docker": "docker",
            "postgresql": "postgresql-server",
            "redis": "redis",
            "go": "golang",
        },
        "pacman": {
            "python": "python",
            "node": "nodejs",
            "docker": "docker",
            "postgresql": "postgresql",
            "redis": "redis",
            "go": "go",
        },
    }

    INSTALL_COMMANDS = {
        "brew": ["brew", "install"],
        "apt": ["sudo", "apt-get", "install", "-y"],
        "dnf": ["sudo", "dnf", "install", "-y"],
        "yum": ["sudo", "yum", "install", "-y"],
        "pacman": ["sudo", "pacman", "-S", "--noconfirm"],
        "apk": ["sudo", "apk", "add"],
        "choco": ["choco", "install", "-y"],
        "winget": ["winget", "install", "--accept-package-agreements"],
        "scoop": ["scoop", "install"],
    }

    def __init__(self, system_info: dict):
        self.system_info = system_info
        self.pkg_manager = system_info["package_manager"]
        self.installed_tools = system_info.get("installed_tools", {})

    def is_installed(self, package_name: str) -> bool:
        """Check if a package/tool is already installed."""
        # Check common binary names
        binary_names = [package_name]

        # Add common binary name variations
        aliases = {
            "node": ["node", "nodejs"],
            "python": ["python3", "python"],
            "postgresql": ["psql", "pg_isready"],
            "docker": ["docker"],
            "redis": ["redis-cli", "redis-server"],
            "go": ["go"],
            "kubectl": ["kubectl"],
            "helm": ["helm"],
            "terraform": ["terraform"],
            "git": ["git"],
            "awscli": ["aws"],
            "conda": ["conda"],
            "jupyter": ["jupyter"],
            "yarn": ["yarn"],
            "pnpm": ["pnpm"],
        }

        binary_names.extend(aliases.get(package_name, []))

        for name in binary_names:
            if shutil.which(name):
                return True
            if name in self.installed_tools:
                return True

        return False

    def install(self, package: Any) -> tuple[bool, str]:
        """Install a package. Returns (success, message)."""
        if isinstance(package, dict):
            return self._install_complex(package)

        return self._install_simple(package)

    def _install_simple(self, package_name: str) -> tuple[bool, str]:
        """Install a simple package by name."""
        # Resolve alias
        resolved = self._resolve_name(package_name)

        # Get install command
        cmd = self.INSTALL_COMMANDS.get(self.pkg_manager)
        if not cmd:
            return False, f"Unknown package manager: {self.pkg_manager}"

        full_cmd = cmd + [resolved]

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                return True, f"Installed {package_name}"
            else:
                error = result.stderr.strip()[:200]
                return False, f"Install failed: {error}"
        except subprocess.TimeoutExpired:
            return False, "Installation timed out (5 min)"
        except FileNotFoundError:
            return False, f"Package manager '{self.pkg_manager}' not found"

    def _install_complex(self, package: dict) -> tuple[bool, str]:
        """Install a package with complex configuration."""
        name = package["name"]
        method = package.get("method", "package_manager")

        if method == "package_manager":
            return self._install_simple(name)

        elif method == "brew_cask":
            return self._run_cmd(["brew", "install", "--cask", name])

        elif method == "npm_global":
            return self._run_cmd(["npm", "install", "-g", name])

        elif method == "pip":
            return self._run_cmd(["pip3", "install", name])

        elif method == "curl":
            url = package.get("url", "")
            if not url:
                return False, "No URL specified for curl install"
            return self._run_cmd(["bash", "-c", f"curl -fsSL {url} | bash"])

        elif method == "custom":
            cmd = package.get("command", "")
            if not cmd:
                return False, "No command specified for custom install"
            return self._run_cmd(["bash", "-c", cmd])

        return False, f"Unknown install method: {method}"

    def _resolve_name(self, package_name: str) -> str:
        """Resolve a generic package name to a package-manager-specific name."""
        aliases = self.PACKAGE_ALIASES.get(self.pkg_manager, {})
        return aliases.get(package_name, package_name)

    def _run_cmd(self, cmd: list[str]) -> tuple[bool, str]:
        """Run a command and return (success, message)."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                return True, "Success"
            return False, result.stderr.strip()[:200]
        except subprocess.TimeoutExpired:
            return False, "Timed out"
        except FileNotFoundError:
            return False, f"Command not found: {cmd[0]}"
