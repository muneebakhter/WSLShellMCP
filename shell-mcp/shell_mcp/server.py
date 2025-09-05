"""FastMCP server implementation for shell command execution."""
import asyncio
import os
import subprocess
import signal
from pathlib import Path
from typing import Optional, Dict, Any

from mcp.server.fastmcp import FastMCP

# Default configuration values
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_OUTPUT = 65536
DEFAULT_WORKDIR = os.getcwd()

def load_config():
    """Load configuration from environment variables."""
    config = {
        'workdir': os.environ.get('SHELL_MCP_WORKDIR', DEFAULT_WORKDIR),
        'timeout': float(os.environ.get('SHELL_MCP_TIMEOUT', str(DEFAULT_TIMEOUT))),
        'max_output': int(os.environ.get('SHELL_MCP_MAX_OUTPUT', str(DEFAULT_MAX_OUTPUT))),
        'sudo_password': os.environ.get('SHELL_MCP_SUDO_PASSWORD'),
        'sudo_password_file': os.environ.get('SHELL_MCP_SUDO_PASSWORD_FILE'),
    }

    # Load sudo password from file if specified
    if config['sudo_password_file'] and not config['sudo_password']:
        try:
            sudo_file_path = Path(config['sudo_password_file']).expanduser()
            if sudo_file_path.exists() and sudo_file_path.is_file():
                config['sudo_password'] = sudo_file_path.read_text().strip()
        except Exception:
            # Silently ignore file reading errors
            pass
    
    return config

# Global configuration loaded from environment variables
config = load_config()

# Create the FastMCP server instance
app = FastMCP("Shell MCP")

@app.tool()
def shell_run(command: str, timeout: Optional[float] = None) -> Dict[str, Any]:
    """
    Execute a shell command using /bin/bash -lc within the configured working directory.
    
    Args:
        command: The shell command to run
        timeout: Optional per-invocation timeout override
        
    Returns:
        Dict with exit_code, stdout, stderr, and truncated flags
    """
    # Reload config to pick up any environment changes
    current_config = load_config()
    
    # Use provided timeout or fall back to configured default
    effective_timeout = timeout if timeout is not None else current_config['timeout']
    
    # Prepare the command
    bash_command = ['/bin/bash', '-lc', command]
    
    # Handle sudo password injection if needed
    stdin_input = None
    if 'sudo' in command and current_config['sudo_password']:
        # Check if -S flag is already present
        if '-S' not in command:
            # Inject -S flag after the first sudo occurrence
            modified_command = command.replace('sudo', 'sudo -S', 1)
            bash_command = ['/bin/bash', '-lc', modified_command]
        stdin_input = current_config['sudo_password'] + '\n'
    
    try:
        # Execute the command
        result = subprocess.run(
            bash_command,
            input=stdin_input,
            capture_output=True,
            text=True,
            cwd=current_config['workdir'],
            timeout=effective_timeout
        )
        
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
        
    except subprocess.TimeoutExpired:
        # Handle timeout
        exit_code = 124  # Standard timeout exit code
        stdout = ""
        stderr = f"Command timed out after {effective_timeout} seconds"
        
    except Exception as e:
        # Handle other execution errors
        exit_code = 1
        stdout = ""
        stderr = f"Execution error: {str(e)}"
    
    # Apply output truncation
    stdout_truncated = len(stdout) > current_config['max_output']
    stderr_truncated = len(stderr) > current_config['max_output']
    
    if stdout_truncated:
        stdout = stdout[:current_config['max_output']]
    if stderr_truncated:
        stderr = stderr[:current_config['max_output']]
    
    return {
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": {
            "stdout": stdout_truncated,
            "stderr": stderr_truncated
        }
    }

def main():
    """Main entry point for the MCP server."""
    app.run()

if __name__ == "__main__":
    main()