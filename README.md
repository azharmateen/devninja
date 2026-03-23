# devninja

One-command dev environment bootstrapper for any OS.

```bash
pip install devninja
devninja setup fullstack
```

## Why devninja?

New machine? New team member? Don't spend half a day installing tools. `devninja` detects your OS, finds your package manager, and installs everything you need from a single preset. It handles packages, VS Code extensions, shell aliases, and PATH configuration.

## Features

- **Cross-platform** - macOS (brew), Ubuntu/Debian (apt), Fedora (dnf), Arch (pacman), Alpine (apk), Windows (choco/winget)
- **5 Built-in Presets** - fullstack, react, python_ml, devops, go_backend
- **Smart Detection** - Skips already-installed tools, detects shell type, finds correct config file
- **VS Code Extensions** - Installs curated extension packs per preset
- **Shell Configuration** - Adds aliases, PATH entries, environment variables with clean delineation
- **Export/Import** - Save your entire env config and restore it on a new machine
- **Dry Run** - Preview everything before installing

## Quickstart

```bash
# Install
pip install devninja

# See available presets
devninja list

# Set up a full-stack environment (dry run first)
devninja setup fullstack --dry-run

# Actually install everything
devninja setup fullstack

# Export your current config
devninja export -o my-env.yaml

# Import on a new machine
devninja import my-env.yaml
```

## Presets

| Preset | Description | Packages |
|--------|-------------|----------|
| `fullstack` | Node.js, Python, Docker, Git, PostgreSQL, Redis | 8 packages + 10 extensions |
| `react` | Node.js, Yarn, Vite, React dev tools | 6 packages + 10 extensions |
| `python_ml` | Python, Conda, Jupyter, NumPy, pandas, scikit-learn | 10 packages + 6 extensions |
| `devops` | Docker, kubectl, Helm, Terraform, AWS CLI, k9s | 11 packages + 5 extensions |
| `go_backend` | Go, Docker, PostgreSQL, Redis, protobuf | 9 packages + 5 extensions |

## CLI Reference

```bash
devninja setup <preset>      # Install a preset
devninja setup <preset> --dry-run    # Preview without installing
devninja setup <preset> --skip-vscode  # Skip VS Code extensions
devninja setup <preset> --force    # Reinstall everything
devninja list                # List available presets
devninja export              # Export current env to YAML
devninja import <file>       # Import env from YAML
```

## Architecture

```
devninja setup fullstack
        |
  [Detector] -- OS, package manager, shell, installed tools
        |
  [Preset Loader] -- fullstack.yaml
        |
  [Installer] -- brew/apt/dnf/pacman install + npm global + pip
        |
  [VSCode Manager] -- code --install-extension
        |
  [Shell Configurator] -- append aliases/PATH/env to .zshrc/.bashrc
```

## License

MIT
