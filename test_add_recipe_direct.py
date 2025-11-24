#!/usr/bin/env python3
"""
Direct test of add_recipe_to_cart prompt without UI
Runs the prompt and execution directly
"""

import sys
sys.path.insert(0, 'src')

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def test_add_recipe():
    """Test the add_recipe_to_cart prompt with direct MCP calls"""
    
    print("=" * 70)
    print("TEST: add_recipe_to_cart Prompt")
    print("=" * 70)
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=['run_server.py'],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to MCP server\n")
            
            # Test 1: Get the prompt
            print("Step 1: Getting the add_recipe_to_cart prompt")
            print("-" * 70)
            try:
                recipe_type = "chocolate chip cookies"
                result = await session.get_prompt(
                    'add_recipe_to_cart', 
                    arguments={'recipe_type': recipe_type}
                )
                
                if result.messages:
                    prompt_text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                    print(f"✅ Prompt generated successfully for '{recipe_type}'")
                    print(f"\nPrompt text:\n{prompt_text}\n")
                else:
                    print("❌ No content returned")
                    return
            except Exception as e:
                print(f"❌ Error getting prompt: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Test 2: Get preferred location
            print("Step 2: Getting preferred location")
            print("-" * 70)
            location_id = None
            try:
                loc_result = await session.call_tool('get_preferred_location', {})
                if loc_result and len(loc_result.content) > 0:
                    loc_text = loc_result.content[0].text if hasattr(loc_result.content[0], 'text') else str(loc_result.content[0])
                    try:
                        loc_json = json.loads(loc_text)
                        location_id = loc_json.get('location_id') or loc_json.get('locationId')
                        print(f"✅ Found preferred location: {location_id}\n")
                    except Exception as e:
                        print(f"⚠️  Could not parse location: {e}")
                        print(f"Response: {loc_text}\n")
            except Exception as e:
                print(f"⚠️  Could not get preferred location: {e}\n")
            
            if not location_id:
                print("⚠️  No preferred location set. Will try to use default.\n")
            
            # Test 3: Search for products
            print("Step 3: Searching for recipe ingredients at Kroger")
            print("-" * 70)
            
            # Example ingredients for chocolate chip cookies
            ingredients = [
                "all-purpose flour",
                "chocolate chips",
                "butter",
                "eggs",
                "brown sugar",
                "vanilla extract",
                "baking soda",
                "salt"
            ]
            
            found_products = []
            
            for ing in ingredients[:5]:  # Limit to 5 for testing
                try:
                    search_args = {"search_term": ing, "limit": 1}
                    if location_id:
                        search_args["location_id"] = location_id
                    
                    search_result = await session.call_tool("search_products", search_args)
                    
                    if search_result and len(search_result.content) > 0:
                        result_text = search_result.content[0].text if hasattr(search_result.content[0], 'text') else str(search_result.content[0])
                        
                        try:
                            result_json = json.loads(result_text)
                            products = result_json.get("data", [])
                            
                            if products:
                                product = products[0]
                                pid = product.get('productId') or product.get('product_id')
                                desc = product.get('description', 'N/A')
                                
                                # Try to get pricing
                                price_str = "N/A"
                                if product.get('items'):
                                    item = product['items'][0]
                                    if item.get('price'):
                                        price_data = item['price']
                                        regular = price_data.get('regular')
                                        sale = price_data.get('promo')
                                        if sale:
                                            price_str = f"${sale:.2f} (was ${regular:.2f})"
                                        elif regular:
                                            price_str = f"${regular:.2f}"
                                
                                print(f"✅ {ing:30s} -> {desc:40s} (ID: {pid}) Price: {price_str}")
                                found_products.append({
                                    "ingredient": ing,
                                    "product_id": pid,
                                    "description": desc
                                })
                            else:
                                print(f"⚠️  {ing:30s} -> No products found")
                        except json.JSONDecodeError as e:
                            print(f"⚠️  {ing:30s} -> Could not parse response: {e}")
                    else:
                        print(f"⚠️  {ing:30s} -> No search result returned")
                        
                except Exception as e:
                    print(f"❌ {ing:30s} -> Error: {str(e)[:80]}")
            
            print()
            
            # Test 4: Try to add to cart
            if found_products:
                print("Step 4: Adding items to cart")
                print("-" * 70)
                
                items_to_add = [
                    {
                        "product_id": p["product_id"],
                        "quantity": 1,
                        "modality": "PICKUP"
                    }
                    for p in found_products
                ]
                
                try:
                    add_result = await session.call_tool("bulk_add_to_cart", {"items": items_to_add})
                    
                    if add_result and len(add_result.content) > 0:
                        result_text = add_result.content[0].text if hasattr(add_result.content[0], 'text') else str(add_result.content[0])
                        
                        try:
                            result_json = json.loads(result_text)
                            if result_json.get("success"):
                                print(f"✅ Successfully added {len(found_products)} item(s) to cart!")
                                print(f"   Response: {json.dumps(result_json, indent=2)[:500]}")
                            else:
                                print(f"⚠️  bulk_add_to_cart returned: {result_json}")
                        except json.JSONDecodeError:
                            print(f"Response: {result_text}")
                    else:
                        print("⚠️  No response from bulk_add_to_cart")
                        
                except Exception as e:
                    print(f"⚠️  Error adding to cart: {e}")
            else:
                print("Step 4: Adding items to cart - SKIPPED (no products found)")
            
            # Test 5: View cart
            print("\nStep 5: Viewing current cart")
            print("-" * 70)
            try:
                cart_result = await session.call_tool("view_current_cart", {})
                
                if cart_result and len(cart_result.content) > 0:
                    result_text = cart_result.content[0].text if hasattr(cart_result.content[0], 'text') else str(cart_result.content[0])
                    
                    try:
                        result_json = json.loads(result_text)
                        if result_json.get("success"):
                            summary = result_json.get("summary", {})
                            print(f"✅ Cart Summary:")
                            print(f"   Total items: {summary.get('total_items', 0)}")
                            print(f"   Total quantity: {summary.get('total_quantity', 0)}")
                            print(f"   Pickup items: {summary.get('pickup_items', 0)}")
                            print(f"   Delivery items: {summary.get('delivery_items', 0)}")
                        else:
                            print(f"Cart info: {result_json}")
                    except json.JSONDecodeError:
                        print(f"Response: {result_text}")
            except Exception as e:
                print(f"⚠️  Error viewing cart: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(test_add_recipe())
