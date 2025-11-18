"""
MCP Server for SSH Operations
"""
import asyncio
import logging
from typing import Dict, Optional
import paramiko
from io import StringIO

logger = logging.getLogger(__name__)

async def execute_ssh_command(
    host: str,
    username: str,
    command: str,
    password: Optional[str] = None,
    private_key: Optional[str] = None,
    port: int = 22,
    use_key: bool = False
) -> Dict:
    """
    Execute a command on a remote host via SSH

    Args:
        host: Target host IP or hostname
        username: SSH username
        command: Command to execute
        password: SSH password (optional if using key)
        private_key: Private key content (optional)
        port: SSH port (default 22)
        use_key: Whether to use SSH key authentication

    Returns:
        Dict with command output and status
    """
    try:
        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Prepare authentication
        connect_kwargs = {
            "hostname": host,
            "port": port,
            "username": username,
            "timeout": 10
        }

        if use_key and private_key:
            # Use private key
            key_file = StringIO(private_key)
            pkey = paramiko.RSAKey.from_private_key(key_file)
            connect_kwargs["pkey"] = pkey
        elif password:
            connect_kwargs["password"] = password
        else:
            # Try default key locations
            connect_kwargs["look_for_keys"] = True

        # Connect
        client.connect(**connect_kwargs)

        # Execute command
        stdin, stdout, stderr = client.exec_command(command, timeout=30)

        # Get output
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_code = stdout.channel.recv_exit_status()

        # Close connection
        client.close()

        return {
            "host": host,
            "command": command,
            "exit_code": exit_code,
            "stdout": output,
            "stderr": error,
            "success": exit_code == 0
        }

    except paramiko.AuthenticationException:
        logger.error(f"Authentication failed for {username}@{host}")
        return {
            "error": "Authentication failed",
            "host": host,
            "success": False
        }
    except paramiko.SSHException as e:
        logger.error(f"SSH error: {e}")
        return {
            "error": f"SSH error: {str(e)}",
            "host": host,
            "success": False
        }
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return {
            "error": str(e),
            "host": host,
            "success": False
        }

async def test_ssh_connection(
    host: str,
    username: str,
    password: Optional[str] = None,
    port: int = 22
) -> Dict:
    """
    Test SSH connection to a host
    """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=5
        )

        client.close()

        return {
            "host": host,
            "status": "connected",
            "success": True
        }

    except Exception as e:
        return {
            "host": host,
            "status": "failed",
            "error": str(e),
            "success": False
        }

async def get_system_info(
    host: str,
    username: str,
    password: Optional[str] = None
) -> Dict:
    """
    Gather system information from a remote host
    """
    commands = {
        "hostname": "hostname",
        "os_info": "cat /etc/os-release 2>/dev/null || uname -a",
        "uptime": "uptime",
        "memory": "free -h",
        "disk": "df -h",
        "cpu": "lscpu | head -20",
        "network": "ip addr show"
    }

    results = {}

    for key, cmd in commands.items():
        result = await execute_ssh_command(
            host=host,
            username=username,
            password=password,
            command=cmd
        )

        if result.get("success"):
            results[key] = result["stdout"]
        else:
            results[key] = f"Error: {result.get('error', 'Unknown error')}"

    return {
        "host": host,
        "system_info": results,
        "success": True
    }

async def transfer_file_sftp(
    host: str,
    username: str,
    password: Optional[str],
    local_path: str,
    remote_path: str,
    upload: bool = True
) -> Dict:
    """
    Transfer files via SFTP
    """
    try:
        transport = paramiko.Transport((host, 22))
        transport.connect(username=username, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport)

        if upload:
            sftp.put(local_path, remote_path)
            action = "uploaded"
        else:
            sftp.get(remote_path, local_path)
            action = "downloaded"

        sftp.close()
        transport.close()

        return {
            "host": host,
            "action": action,
            "local_path": local_path,
            "remote_path": remote_path,
            "success": True
        }

    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }
