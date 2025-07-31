#!/usr/bin/env python3
"""
System information and diagnostics for App Service MCP debugging
"""
import os
import subprocess
import platform


def run_command(command):
    """Run a system command and return output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return f"Exit code: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Error running command: {e}"


def test_system_info():
    """Collect system information and network diagnostics"""
    print("=== System Information ===")
    print(f"Platform: {platform.platform()}")
    print(f"Python version: {platform.python_version()}")
    print(f"Python executable: {os.sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    
    print("\n=== Environment Variables ===")
    azure_vars = [
        'AZURE_AI_PROJECT_ENDPOINT',
        'AZURE_AI_PROJECT_NAME', 
        'AZURE_OPENAI_DEPLOYMENT_NAME',
        'AZURE_APP_SERVICE_URL',
        'WEBSITE_HOSTNAME',
        'WEBSITE_SITE_NAME'
    ]
    
    for var in azure_vars:
        value = os.getenv(var, 'NOT SET')
        print(f"{var}: {value}")
    
    print("\n=== Process Information ===")
    print(run_command("ps aux | grep python"))
    
    print("\n=== Network Information ===")
    print("--- Listening ports ---")
    print(run_command("netstat -tlnp | grep :8000"))
    
    print("\n--- DNS resolution ---")
    print(run_command("nslookup localhost"))
    
    print("\n--- Localhost connectivity ---")
    print(run_command("curl -I http://localhost:8000/health"))
    
    print("\n--- External connectivity ---")
    app_url = os.getenv('AZURE_APP_SERVICE_URL', 'https://az-tda-app-wgznky2irncfe.azurewebsites.net')
    print(run_command(f"curl -I {app_url}/health"))
    
    print("\n=== File System ===")
    print("--- Current directory contents ---")
    print(run_command("ls -la"))
    
    print("\n--- Python packages ---")
    print(run_command("pip list | grep -E '(azure|requests|fastapi)'"))


if __name__ == "__main__":
    test_system_info()
