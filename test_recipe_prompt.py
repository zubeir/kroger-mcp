#!/usr/bin/env python3
"""Direct test of the add_recipe_to_cart prompt"""

import sys
sys.path.insert(0, 'src')
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    print("=== Testing add_recipe_to_cart prompt ===\n")
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=['run_server.py'],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("Test 1: List all prompts")
            try:
                prompts_result = await session.list_prompts()
                if prompts_result and prompts_result.prompts:
                    print(f"✅ Found {len(prompts_result.prompts)} prompts:")
                    for p in prompts_result.prompts:
                        print(f"  - {p.name}")
                else:
                    print("❌ No prompts found")
            except Exception as e:
                print(f"❌ Error listing prompts: {e}")
                import traceback
                traceback.print_exc()
            
            print("\nTest 2: Get add_recipe_to_cart with arguments")
            try:
                result = await session.get_prompt('add_recipe_to_cart', arguments={'recipe_type': 'chocolate chip cookies'})
                print("✅ Success with arguments!")
                if result.messages:
                    text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                    print(f"Prompt text (first 200 chars): {text[:200]}")
            except Exception as e:
                print(f"❌ Error with arguments: {e}")
                import traceback
                traceback.print_exc()
            
            print("\nTest 3: Get add_recipe_to_cart without arguments")
            try:
                result = await session.get_prompt('add_recipe_to_cart')
                print("✅ Success without arguments!")
                if result.messages:
                    text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                    print(f"Prompt text (first 200 chars): {text[:200]}")
            except Exception as e:
                print(f"❌ Error without arguments: {e}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
