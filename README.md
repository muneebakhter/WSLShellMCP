# Shell MCP

A minimal Model Context Protocol (MCP) server that exposes a safe, configurable way to run shell commands via a single tool: `shell_run`.

It uses `/bin/bash -lc` under the hood, supports a configurable working directory, timeouts, output truncation, and optional `sudo` with password injection.

> Note: This repo contains the MCP server code in `shell-mcp/shell_mcp`. You typically run this server from inside the `shell-mcp/` folder.

---

## Features

- `shell_run` tool: Execute commands with `/bin/bash -lc`.
- Controlled environment:
  - Working directory: `SHELL_MCP_WORKDIR` (defaults to current directory on launch)
  - Timeout per command: `SHELL_MCP_TIMEOUT` (default: `120` seconds)
  - Output truncation: `SHELL_MCP_MAX_OUTPUT` (default: `65536` bytes)
- Optional `sudo` support:
  - If a `sudo` password is provided, the server injects `-S` and writes the password to stdin for commands including `sudo`.
  - Password can be set directly with `SHELL_MCP_SUDO_PASSWORD` or read from file via `SHELL_MCP_SUDO_PASSWORD_FILE`.
- Stdio MCP server built with `FastMCP` from the `mcp` library.

---

## Project layout

```
WSLShellMCP/
├─ README.md                 # This file
└─ shell-mcp/
   ├─ requirements.txt       # pip dependencies (mcp >= 1.13.0)
   └─ shell_mcp/
      ├─ __init__.py
      ├─ __main__.py         # Entry point: `python -m shell_mcp`
      └─ server.py           # FastMCP server exposing `shell_run`
```

---

## Prerequisites

- Python 3.8+ (virtual environment recommended)
- A Linux-compatible shell (`/bin/bash`) — works on Linux and WSL

---

## Quick start

1) Clone and enter the project directory

```bash
git clone https://github.com/muneebakhter/WSLShellMCP.git
cd WSLShellMCP/shell-mcp
```

2) Create and activate a virtual environment (optional but recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3) Install dependencies

```bash
pip install -r requirements.txt
```

4) Run the MCP server (stdio)

```bash
python -m shell_mcp
```

This process runs an MCP server over stdio. In practice, an MCP-compatible client (e.g., an editor or app that speaks MCP) will launch and communicate with this server automatically.

---

## Configuration

Configure behavior via environment variables:

- `SHELL_MCP_WORKDIR` (string):
  - Directory to execute commands in. Defaults to the process working directory.
- `SHELL_MCP_TIMEOUT` (float, seconds):
  - Per-command timeout. Default: `120`.
- `SHELL_MCP_MAX_OUTPUT` (int, bytes):
  - Truncation limit for `stdout` and `stderr`. Default: `65536`.
- `SHELL_MCP_SUDO_PASSWORD` (string):
  - If set, commands containing `sudo` will have `-S` injected (if missing) and the password is written to stdin.
- `SHELL_MCP_SUDO_PASSWORD_FILE` (string, path):
  - Alternative to the above—if provided and readable, the server loads the sudo password from this file.

Example (Linux/WSL):

```bash
export SHELL_MCP_WORKDIR="$HOME"
export SHELL_MCP_TIMEOUT=180
export SHELL_MCP_MAX_OUTPUT=$((128 * 1024))
# Choose ONE of the following options (prefer the file for security):
# export SHELL_MCP_SUDO_PASSWORD='your-password-here'
export SHELL_MCP_SUDO_PASSWORD_FILE="$HOME/.config/shell-mcp/sudo.pw"
python -m shell_mcp
```

Security tips:
- Avoid putting sudo passwords directly into shell histories; prefer using a file with restrictive permissions (e.g., `chmod 600`).
- Use least-privilege—only provide `sudo` when absolutely necessary.

---

## Tool: `shell_run`

Description:
- Execute a shell command using `/bin/bash -lc` within the configured working directory.
- Returns a JSON-like result with `exit_code`, `stdout`, `stderr`, and `truncated` flags.

Input parameters:
- `command` (string): the shell command to run.
- `timeout` (optional float): per-invocation override for `SHELL_MCP_TIMEOUT`.

Behavior notes:
- If `sudo` is present in the command and a password is configured, the server injects `-S` (if not already present) and writes the password to stdin.
- Output may be truncated if it exceeds `SHELL_MCP_MAX_OUTPUT`.
- On timeout, the process is killed and `exit_code` is set to `124`, with a note appended to `stderr`.

---

## Using with an MCP client

This server speaks standard MCP over stdio. Typical integration patterns:

- Tools that support MCP (e.g., editor integrations) can launch the server with `python -m shell_mcp` and communicate over stdio.
- Ensure the environment variables above are set in the client’s launch environment if you need custom behavior.

Since MCP client configuration varies by tool, consult your client’s documentation for how to register an MCP server executable.

---

## Troubleshooting

- Command times out (exit code 124):
  - Increase `SHELL_MCP_TIMEOUT` or pass a higher `timeout` to `shell_run`.
- Output truncated:
  - Increase `SHELL_MCP_MAX_OUTPUT`.
- `sudo` prompts for a password:
  - Set `SHELL_MCP_SUDO_PASSWORD` or `SHELL_MCP_SUDO_PASSWORD_FILE`. Ensure the command includes `sudo` (the server injects `-S` automatically for the first `sudo`).
- Permission denied / working directory issues:
  - Verify `SHELL_MCP_WORKDIR` exists and you have the necessary permissions.

---

## Development

- Code lives in `shell-mcp/shell_mcp/`.
- Entry point is `__main__.py` which calls `server.main()`.
- The server implementation is in `server.py`, built on `FastMCP` from the `mcp` package.

---

## License

No license file is currently provided. If you plan to distribute or modify, consider adding a license (e.g., MIT, Apache-2.0).
