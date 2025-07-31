#!/usr/bin/env python3
"""
Run all MCP diagnostic tests
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_system_info import test_system_info
from test_mcp_local import test_mcp_connection
from test_mcp_external import test_external_mcp
from test_azure_ai import test_azure_ai_mcp


def main():
    """Run all diagnostic tests"""
    print("🔍 Starting MCP Diagnostic Tests")
    print("=" * 60)
    
    try:
        print("\n📊 1. System Information")
        print("-" * 30)
        test_system_info()
        
        print("\n🔧 2. Local MCP Tests")
        print("-" * 30)
        test_mcp_connection()
        
        print("\n🌐 3. External MCP Tests")
        print("-" * 30)
        test_external_mcp()
        
        print("\n☁️ 4. Azure AI Tests")
        print("-" * 30)
        test_azure_ai_mcp()
        
        print("\n" + "=" * 60)
        print("✅ All diagnostic tests completed!")
        print("Check the output above for any ❌ errors or issues.")
        
    except Exception as e:
        print(f"\n❌ Error running diagnostic tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
