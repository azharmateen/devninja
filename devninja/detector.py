"""Detect OS, package manager, shell, and existing tools."""

import os
import platform
import shutil
import subprocess


class SystemDetector:
    """Detect the current system configuration."""

    def detect(self) -> dict:
        """Detect all system properties."""
        os_type = self._detect_os()
        return {
            "os": os_type,
            "os_version": platform.version(),
            "arch": platform.machine(),
            "package_manager": self._detect_package_manager(os_type),
            "shell": self._detect_shell(),
            "shell_config": self._detect_shell_config(),
            "installed_tools": self._detect_installed_tools(),
            "home": os.path.expanduser("~"),
        }

    def _detect_os(self) -> str:
        """Detect the operating system."""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "linux":
            return self._detect_linux_distro()
        elif system == "windows":
            return "windows"
        return system

    def _detect_linux_distro(self) -> str:
        """Detect the Linux distribution."""
        try:
            with open("/etc/os-release") as f:
                content = f.read().lower()
                if "ubuntu" in content or "debian" in content:
                    return "ubuntu"
                elif "fedora" in content:
                    return "fedora"
                elif "centos" in content or "rhel" in content or "red hat" in content:
                    return "centos"
                elif "arch" in content:
                    return "arch"
                elif "alpine" in content:
                    return "alpine"
                elif "opensuse" in content or "suse" in content:
                    return "suse"
        except FileNotFoundError:
            pass
        return "linux"

    def _detect_package_manager(self, os_type: str) -> str:
        """Detect the primary package manager."""
        # Check in priority order
        managers = {
            "macos": [("brew", "brew")],
            "ubuntu": [("apt", "apt-get"), ("snap", "snap")],
            "fedora": [("dnf", "dnf"), ("yum", "yum")],
            "centos": [("yum", "yum"), ("dnf", "dnf")],
            "arch": [("pacman", "pacman")],
            "alpine": [("apk", "apk")],
            "suse": [("zypper", "zypper")],
            "windows": [("choco", "choco"), ("winget", "winget"), ("scoop", "scoop")],
        }

        candidates = managers.get(os_type, [])
        for name, cmd in candidates:
            if shutil.which(cmd):
                return name

        # Fallback detection
        for name, cmd in [("brew", "brew"), ("apt", "apt-get"), ("yum", "yum"),
                          ("dnf", "dnf"), ("pacman", "pacman"), ("apk", "apk")]:
            if shutil.which(cmd):
                return name

        return "unknown"

    def _detect_shell(self) -> str:
        """Detect the current shell."""
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            return "zsh"
        elif "bash" in shell:
            return "bash"
        elif "fish" in shell:
            return "fish"
        elif "powershell" in shell.lower() or "pwsh" in shell.lower():
            return "powershell"

        # Fallback
        if shutil.which("zsh"):
            return "zsh"
        if shutil.which("bash"):
            return "bash"
        return "sh"

    def _detect_shell_config(self) -> str:
        """Detect the shell configuration file path."""
        shell = self._detect_shell()
        home = os.path.expanduser("~")

        config_map = {
            "zsh": os.path.join(home, ".zshrc"),
            "bash": os.path.join(home, ".bashrc"),
            "fish": os.path.join(home, ".config", "fish", "config.fish"),
            "powershell": os.path.join(home, "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1"),
        }

        config = config_map.get(shell, os.path.join(home, ".bashrc"))

        # macOS uses .bash_profile for login shells
        if shell == "bash" and platform.system() == "Darwin":
            bash_profile = os.path.join(home, ".bash_profile")
            if os.path.exists(bash_profile):
                config = bash_profile

        return config

    def _detect_installed_tools(self) -> dict[str, str]:
        """Detect already installed development tools and their versions."""
        tools = [
            "node", "npm", "yarn", "pnpm", "bun",
            "python3", "pip", "pip3", "conda",
            "go", "rustc", "cargo",
            "docker", "docker-compose", "kubectl", "helm", "terraform",
            "git", "gh", "code",
            "java", "mvn", "gradle",
            "ruby", "gem",
            "aws", "gcloud", "az",
        ]

        installed = {}
        for tool in tools:
            path = shutil.which(tool)
            if path:
                version = self._get_version(tool)
                installed[tool] = version

        return installed

    def _get_version(self, tool: str) -> str:
        """Get the version string for a tool."""
        version_flags = {
            "go": ["go", "version"],
            "java": ["java", "-version"],
            "rustc": ["rustc", "--version"],
        }

        cmd = version_flags.get(tool, [tool, "--version"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = (result.stdout or result.stderr or "").strip()
            # Extract just the version number from the first line
            first_line = output.split("\n")[0]
            return first_line[:80]
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return "installed"
