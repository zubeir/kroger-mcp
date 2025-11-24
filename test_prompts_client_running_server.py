#!/usr/bin/env python3
"""
Test client for Kroger MCP Prompts - Testing against a running server

This script:
1. Connects to an already-running Kroger MCP server
2. Tests all 4 registered prompts via MCP protocol
3. Displays results for each prompt

Usage Options:

Option 1: Connect to server via stdio (starts server automatically)
    python test_prompts_client_running_server.py

Option 2: Connect to server running with SSE transport
    # Terminal 1: Start server with SSE
    python -m kroger_mcp.cli --transport sse --port 8000
    
    # Terminal 2: Run this test client
    python test_prompts_client_running_server.py --transport sse --port 8000
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path to import kroger_mcp
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import path
        from mcp.client import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        MCP_AVAILABLE = True
    except ImportError:
        print("❌ MCP SDK not available. Please install with: pip install mcp")
        print("   This script requires the MCP SDK to connect to a running server.")
        sys.exit(1)


async def test_prompts_against_running_server(transport: str = "stdio", host: str = "127.0.0.1", port: int = 8000):
    """Test all 4 prompts against a running MCP server"""
    print("\n" + "="*60)
    print("🛒 Kroger MCP Prompts Test Client")
    print("   Testing against running server")
    print("="*60)
    
    # Get the path to run_server.py
    server_script = Path(__file__).parent / "run_server.py"
    if not server_script.exists():
        print(f"❌ Error: {server_script} not found!")
        return {}
    
    print(f"\n🔌 Connecting to MCP server via {transport}...")
    
    if transport == "sse":
        print(f"   Server should be running with: python -m kroger_mcp.cli --transport sse --port {port}")
        print(f"   Connecting to: http://{host}:{port}")
        print("\n⚠️  Note: SSE transport connection not yet implemented in this script.")
        print("   Please use stdio transport or implement SSE client connection.")
        return {}
    
    try:
        # Create stdio client connection
        # Note: stdio_client will start the server automatically
        # If you want to connect to an already-running server, use SSE or HTTP transport
        # and implement the appropriate client connection
        
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(server_script)],
            env=os.environ.copy()
        )
        
        print("📡 Establishing connection via stdio...")
        print("   (This will start the server automatically)")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                print("🔧 Initializing MCP session...")
                await session.initialize()
                
                # List available prompts
                print("\n📋 Listing available prompts...")
                prompts_result = await session.list_prompts()
                
                if not prompts_result.prompts:
                    print("❌ No prompts found on the server!")
                    return {}
                
                print(f"✅ Found {len(prompts_result.prompts)} prompts:")
                for prompt in prompts_result.prompts:
                    print(f"   - {prompt.name}")
                    if prompt.description:
                        print(f"     Description: {prompt.description}")
                
                # Test each prompt
                test_results = {}
                
                # 1. Test grocery_list_store_path
                print(f"\n{'='*60}")
                print("🧪 Testing Prompt: grocery_list_store_path")
                print(f"{'='*60}")
                grocery_list = """- Milk
- Bread
- Eggs
- Chicken breast
- Tomatoes
- Lettuce
- Bananas"""
                
                try:
                    result = await session.get_prompt(
                        "grocery_list_store_path",
                        arguments={"grocery_list": grocery_list}
                    )
                    if result.messages and len(result.messages) > 0:
                        prompt_text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                        print(f"\n📋 Prompt Result:\n{prompt_text}")
                        test_results["grocery_list_store_path"] = True
                        print("✅ PASS")
                    else:
                        print("⚠️  No content returned")
                        test_results["grocery_list_store_path"] = False
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    test_results["grocery_list_store_path"] = False
                
                # 2. Test pharmacy_open_check
                print(f"\n{'='*60}")
                print("🧪 Testing Prompt: pharmacy_open_check")
                print(f"{'='*60}")
                try:
                    result = await session.get_prompt("pharmacy_open_check")
                    if result.messages and len(result.messages) > 0:
                        prompt_text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                        print(f"\n📋 Prompt Result:\n{prompt_text}")
                        test_results["pharmacy_open_check"] = True
                        print("✅ PASS")
                    else:
                        print("⚠️  No content returned")
                        test_results["pharmacy_open_check"] = False
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    test_results["pharmacy_open_check"] = False
                
                # 3. Test set_preferred_store
                print(f"\n{'='*60}")
                print("🧪 Testing Prompt: set_preferred_store")
                print(f"{'='*60}")
                try:
                    result = await session.get_prompt(
                        "set_preferred_store",
                        arguments={"zip_code": "45202"}
                    )
                    if result.messages and len(result.messages) > 0:
                        prompt_text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                        print(f"\n📋 Prompt Result:\n{prompt_text}")
                        test_results["set_preferred_store"] = True
                        print("✅ PASS")
                    else:
                        print("⚠️  No content returned")
                        test_results["set_preferred_store"] = False
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    test_results["set_preferred_store"] = False
                
                # 4. Test add_recipe_to_cart
                print(f"\n{'='*60}")
                print("🧪 Testing Prompt: add_recipe_to_cart")
                print(f"{'='*60}")
                try:
                    result = await session.get_prompt(
                        "add_recipe_to_cart",
                        arguments={"recipe_type": "chocolate chip cookies"}
                    )
                    if result.messages and len(result.messages) > 0:
                        prompt_text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                        print(f"\n📋 Prompt Result:\n{prompt_text}")
                        test_results["add_recipe_to_cart"] = True
                        print("✅ PASS")
                    else:
                        print("⚠️  No content returned")
                        test_results["add_recipe_to_cart"] = False
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    test_results["add_recipe_to_cart"] = False
                
                return test_results
                
    except Exception as e:
        print(f"\n❌ Error connecting to MCP server: {e}")
        print("\n💡 Make sure the server is running:")
        print("   python run_server.py")
        import traceback
        traceback.print_exc()
        return {}


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test Kroger MCP prompts against a running server"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for SSE transport (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000)"
    )
    
    args = parser.parse_args()
    
    try:
        test_results = await test_prompts_against_running_server(
            transport=args.transport,
            host=args.host,
            port=args.port
        )
        
        if not test_results:
            print("\n❌ No tests completed. Check server connection.")
            return
        
        # Print summary
        print("\n" + "="*60)
        print("📊 Test Summary")
        print("="*60)
        for prompt_name, success in test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {prompt_name}")
        
        total = len(test_results)
        passed = sum(test_results.values())
        print(f"\nTotal: {passed}/{total} prompts tested successfully")
        
        if passed == total:
            print("🎉 All prompts tested successfully!")
        else:
            print("⚠️  Some prompts failed. Check the output above for details.")
        
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

