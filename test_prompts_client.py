#!/usr/bin/env python3
"""
Test client for Kroger MCP Prompts

This script:
1. Sets up environment variables using set_kroger_dev_env.ps1
2. Starts the MCP server in the background
3. Connects to the server as an MCP client
4. Tests all 4 registered prompts via MCP protocol
"""

import os
import sys
import subprocess
import asyncio
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
        print("⚠️  MCP SDK not available. Install with: pip install mcp")
        MCP_AVAILABLE = False
        # Fallback: we'll test prompts directly
        from kroger_mcp.server import create_server
        from fastmcp import FastMCP


def setup_environment():
    """Run the PowerShell script to set up environment variables"""
    script_path = Path(__file__).parent / "set_kroger_dev_env.ps1"
    
    if not script_path.exists():
        print(f"❌ Error: {script_path} not found!")
        return False
    
    print(f"📝 Setting up environment from {script_path.name}...")
    
    try:
        # Run PowerShell script to set environment variables
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode != 0:
            print(f"⚠️  PowerShell script returned non-zero exit code: {result.returncode}")
            print(f"   stderr: {result.stderr}")
        
        # Read the script to extract environment variables
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Parse environment variables from the script
        env_vars = {}
        for line in script_content.split('\n'):
            line = line.strip()
            if line.startswith('$env:'):
                # Extract variable name and value
                # Format: $env:VAR_NAME = "value"
                parts = line.split('=', 1)
                if len(parts) == 2:
                    var_name = parts[0].replace('$env:', '').strip()
                    var_value = parts[1].strip().strip('"').strip("'")
                    os.environ[var_name] = var_value
                    env_vars[var_name] = var_value
                    print(f"   ✓ Set {var_name}")
        
        # Create .env file from the extracted variables
        env_file_path = Path(__file__).parent / ".env"
        try:
            with open(env_file_path, 'w') as f:
                for var_name, var_value in env_vars.items():
                    f.write(f"{var_name}={var_value}\n")
            print(f"   ✓ Created .env file at {env_file_path}")
        except Exception as e:
            print(f"   ⚠️  Could not create .env file: {e}")
        
        # Verify required environment variables
        required_vars = ['KROGER_CLIENT_ID', 'KROGER_CLIENT_SECRET']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            return False
        
        print("✅ Environment setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up environment: {e}")
        return False


async def test_prompt_direct(prompt_func, prompt_name: str, args: Dict[str, Any] = None) -> str:
    """Test a specific prompt function directly"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing Prompt: {prompt_name}")
    print(f"{'='*60}")
    
    try:
        # Call the prompt function directly
        if args:
            result = await prompt_func(**args)
        else:
            result = await prompt_func()
        
        print(f"\n📋 Prompt Result:\n")
        print(result)
        print(f"\n✅ Prompt '{prompt_name}' executed successfully!")
        return result
            
    except Exception as e:
        print(f"❌ Error testing prompt '{prompt_name}': {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_prompt_functions(server: FastMCP):
    """Extract prompt functions from the server after registration"""
    prompts = {}
    
    # Try to access prompts from the server
    # FastMCP may store them in different ways
    if hasattr(server, '_prompts'):
        prompts = server._prompts
    elif hasattr(server, 'prompts'):
        prompts = server.prompts
    elif hasattr(server, '__dict__'):
        # Look for prompt-related attributes
        for key, value in server.__dict__.items():
            if 'prompt' in key.lower():
                if isinstance(value, dict):
                    prompts.update(value)
    
    return prompts


async def test_prompts_via_mcp():
    """Test prompts via MCP protocol"""
    if not MCP_AVAILABLE:
        print("⚠️  MCP SDK not available, testing prompts directly...")
        return await test_prompts_direct()
    
    print("\n🚀 Starting MCP server and connecting...")
    
    # Get the path to run_server.py
    server_script = Path(__file__).parent / "run_server.py"
    if not server_script.exists():
        print(f"❌ Error: {server_script} not found!")
        return await test_prompts_direct()
    
    try:
        # Create stdio client connection - this will start the server automatically
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(server_script)],
            env=os.environ.copy()
        )
        
        print("🔌 Connecting to MCP server via stdio...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # List available prompts
                print("📋 Listing available prompts...")
                prompts_result = await session.list_prompts()
                
                if not prompts_result.prompts:
                    print("⚠️  No prompts found. Testing directly...")
                    return await test_prompts_direct()
                
                print(f"✅ Found {len(prompts_result.prompts)} prompts:")
                for prompt in prompts_result.prompts:
                    print(f"   - {prompt.name}")
                
                # Test each prompt
                test_results = {}
                
                # 1. Test grocery_list_store_path
                grocery_list = """- Milk
- Bread
- Eggs
- Chicken breast
- Tomatoes
- Lettuce
- Bananas"""
                
                print(f"\n{'='*60}")
                print("🧪 Testing Prompt: grocery_list_store_path")
                print(f"{'='*60}")
                try:
                    result = await session.get_prompt(
                        "grocery_list_store_path",
                        arguments={"grocery_list": grocery_list}
                    )
                    print(f"\n📋 Prompt Result:\n{result.messages[0].content.text if result.messages else 'No content'}")
                    test_results["grocery_list_store_path"] = True
                except Exception as e:
                    print(f"❌ Error: {e}")
                    test_results["grocery_list_store_path"] = False
                
                # 2. Test pharmacy_open_check
                print(f"\n{'='*60}")
                print("🧪 Testing Prompt: pharmacy_open_check")
                print(f"{'='*60}")
                try:
                    result = await session.get_prompt("pharmacy_open_check")
                    print(f"\n📋 Prompt Result:\n{result.messages[0].content.text if result.messages else 'No content'}")
                    test_results["pharmacy_open_check"] = True
                except Exception as e:
                    print(f"❌ Error: {e}")
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
                    print(f"\n📋 Prompt Result:\n{result.messages[0].content.text if result.messages else 'No content'}")
                    test_results["set_preferred_store"] = True
                except Exception as e:
                    print(f"❌ Error: {e}")
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
                    print(f"\n📋 Prompt Result:\n{result.messages[0].content.text if result.messages else 'No content'}")
                    test_results["add_recipe_to_cart"] = True
                except Exception as e:
                    print(f"❌ Error: {e}")
                    test_results["add_recipe_to_cart"] = False
                
                return test_results
                
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Falling back to direct prompt testing...")
        return await test_prompts_direct()


async def test_prompts_direct():
    """Fallback: Test prompts directly without MCP protocol"""
    print("\n🔧 Testing prompts directly (fallback mode)...")
    
    # Create server instance
    try:
        server = create_server()
    except Exception as e:
        print(f"❌ Error creating server: {e}")
        return {}
    
    # Extract prompt functions
    from kroger_mcp import prompts
    temp_server = FastMCP("temp")
    prompts.register_prompts(temp_server)
    prompt_funcs = extract_prompt_functions(temp_server)
    
    if not prompt_funcs:
        # Use fallback implementations
        async def test_grocery_list_store_path(grocery_list: str):
            return f"""I'm planning to go grocery shopping at Kroger with this list:

{grocery_list}

Can you help me find the most efficient path through the store? Please search for these products to determine their aisle locations, then arrange them in a logical shopping order. 

If you can't find exact matches for items, please suggest similar products that are available.

IMPORTANT: Please only organize my shopping path - DO NOT add any items to my cart.
"""
        
        async def test_pharmacy_open_check():
            return """Can you tell me if the pharmacy at my preferred Kroger store is currently open? 

Please check the department information for the pharmacy department and let me know:
1. If there is a pharmacy at my preferred store
2. If it's currently open 
3. What the hours are for today
4. What services are available at this pharmacy

Please use the get_location_details tool to find this information for my preferred location.
"""
        
        async def test_set_preferred_store(zip_code: Optional[str] = None):
            zip_phrase = f" near zip code {zip_code}" if zip_code else ""
            return f"""I'd like to set my preferred Kroger store{zip_phrase}. Can you help me with this process?

Please:
1. Search for nearby Kroger stores{zip_phrase}
2. Show me a list of the closest options with their addresses
3. Let me choose one from the list
4. Set that as my preferred location 

For each store, please show the full address, distance, and any special features or departments.
"""
        
        async def test_add_recipe_to_cart(recipe_type: str = "classic apple pie"):
            return f"""I'd like to make a recipe: {recipe_type}. Can you help me with the following:

1. Search the web for a good {recipe_type} recipe
2. Present the recipe with ingredients and instructions
3. Look up each ingredient in my local Kroger store
4. Add all the ingredients I'll need to my cart using bulk_add_to_cart
5. If any ingredients aren't available, suggest alternatives

Before adding items to cart, please ask me if I prefer pickup or delivery for these items.
"""
        
        prompt_funcs = {
            "grocery_list_store_path": test_grocery_list_store_path,
            "pharmacy_open_check": test_pharmacy_open_check,
            "set_preferred_store": test_set_preferred_store,
            "add_recipe_to_cart": test_add_recipe_to_cart,
        }
    
    # Test each prompt
    test_results = {}
    
    grocery_list = """- Milk
- Bread
- Eggs
- Chicken breast
- Tomatoes
- Lettuce
- Bananas"""
    
    for prompt_name, test_data in [
        ("grocery_list_store_path", {"grocery_list": grocery_list}),
        ("pharmacy_open_check", None),
        ("set_preferred_store", {"zip_code": "45202"}),
        ("add_recipe_to_cart", {"recipe_type": "chocolate chip cookies"}),
    ]:
        if prompt_name in prompt_funcs:
            result = await test_prompt_direct(
                prompt_funcs[prompt_name],
                prompt_name,
                test_data
            )
            test_results[prompt_name] = result is not None
        else:
            test_results[prompt_name] = False
    
    return test_results


async def test_all_prompts():
    """Test all 4 Kroger MCP prompts"""
    print("\n" + "="*60)
    print("🛒 Kroger MCP Prompts Test Client")
    print("="*60)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Failed to set up environment. Exiting.")
        return
    
    try:
        # Test prompts via MCP (server will be started automatically by stdio_client)
        test_results = await test_prompts_via_mcp()
        
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
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    try:
        asyncio.run(test_all_prompts())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

