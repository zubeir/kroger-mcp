#!/usr/bin/env python3
"""
Complete test of add_recipe_to_cart with location setup
Simplified for Windows console compatibility
"""

import sys
sys.path.insert(0, 'src')

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def test_add_recipe_complete():
    """Complete test: set location, search products, add to cart"""
    
    print("=" * 70)
    print("COMPLETE TEST: add_recipe_to_cart with Location Setup")
    print("=" * 70)
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=['run_server.py'],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[OK] Connected to MCP server\n")
            
            # Step 1: Find locations near a zip code
            print("Step 1: Finding Kroger stores near zip code 45202")
            print("-" * 70)
            
            location_id = None
            try:
                loc_search = await session.call_tool(
                    "search_locations",
                    {"zip_code": "45202", "limit": 1}
                )
                
                if loc_search and len(loc_search.content) > 0:
                    loc_text = loc_search.content[0].text if hasattr(loc_search.content[0], 'text') else str(loc_search.content[0])
                    
                    try:
                        loc_json = json.loads(loc_text)
                        locations = loc_json.get("data", [])
                        
                        if locations:
                            location = locations[0]
                            location_id = location.get("locationId") or location.get("location_id")
                            name = location.get("name", "Unknown")
                            address = location.get("address", {}).get("address_line1", "N/A")
                            print("[OK] Found: " + name)
                            print("     Address: " + address)
                            print("     Location ID: " + str(location_id) + "\n")
                    except json.JSONDecodeError as e:
                        print("[ERROR] Could not parse location response: " + str(e) + "\n")
            except Exception as e:
                print("[ERROR] Error searching locations: " + str(e) + "\n")
            
            if not location_id:
                print("❌ Could not find a store location. Exiting.\n")
                return
            
            # Step 2: Get the prompt
            print("Step 2: Getting the add_recipe_to_cart prompt")
            print("-" * 70)
            try:
                recipe_type = "chocolate chip cookies"
                result = await session.get_prompt(
                    'add_recipe_to_cart', 
                    arguments={'recipe_type': recipe_type}
                )
                
                if result.messages:
                    prompt_text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                    print("[OK] Prompt generated successfully for '" + recipe_type + "'")
                    print("\nPrompt:\n" + prompt_text + "\n")
            except Exception as e:
                print("[ERROR] Error getting prompt: " + str(e) + "\n")
                return
            
            # Step 3: Search for products with the location
            print("Step 3: Searching for recipe ingredients at location {0}".format(location_id))
            print("-" * 70)
            
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
            
            for ing in ingredients:
                try:
                    search_result = await session.call_tool(
                        "search_products",
                        {
                            "search_term": ing,
                            "location_id": location_id,
                            "limit": 1
                        }
                    )
                    
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
                                
                                print(f"✅ {ing:25s} -> {desc[:45]:45s} (${price_str})")
                                found_products.append({
                                    "ingredient": ing,
                                    "product_id": pid,
                                    "description": desc,
                                    "price": price_str
                                })
                            else:
                                print(f"⚠️  {ing:25s} -> No products found")
                        except json.JSONDecodeError as e:
                            print(f"⚠️  {ing:25s} -> Could not parse: {str(e)[:40]}")
                    else:
                        print(f"⚠️  {ing:25s} -> No search result")
                        
                except Exception as e:
                    print(f"❌ {ing:25s} -> Error: {str(e)[:60]}")
            
            print()
            
            # Step 4: Add to cart
            if found_products:
                print(f"Step 4: Adding {len(found_products)} item(s) to cart")
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
                    add_result = await session.call_tool(
                        "bulk_add_to_cart",
                        {"items": items_to_add}
                    )
                    
                    if add_result and len(add_result.content) > 0:
                        result_text = add_result.content[0].text if hasattr(add_result.content[0], 'text') else str(add_result.content[0])
                        
                        try:
                            result_json = json.loads(result_text)
                            if result_json.get("success"):
                                print(f"✅ Successfully added {result_json.get('items_added', len(found_products))} item(s) to cart!")
                            else:
                                print(f"⚠️  Response: {json.dumps(result_json, indent=2)[:300]}")
                        except json.JSONDecodeError:
                            print(f"Response: {result_text[:200]}")
                    else:
                        print("⚠️  No response from bulk_add_to_cart")
                        
                except Exception as e:
                    print(f"⚠️  Error adding to cart: {e}")
                    
                print()
            else:
                print("Step 4: Adding items to cart - SKIPPED (no products found)\n")
            
            # Step 5: View cart
            print("Step 5: Viewing current cart")
            print("-" * 70)
            try:
                cart_result = await session.call_tool("view_current_cart", {})
                
                if cart_result and len(cart_result.content) > 0:
                    result_text = cart_result.content[0].text if hasattr(cart_result.content[0], 'text') else str(cart_result.content[0])
                    
                    try:
                        result_json = json.loads(result_text)
                        if result_json.get("success"):
                            summary = result_json.get("summary", {})
                            cart_items = result_json.get("current_cart", [])
                            
                            print(f"✅ Cart Summary:")
                            print(f"   Total items in cart: {summary.get('total_items', 0)}")
                            print(f"   Total quantity: {summary.get('total_quantity', 0)}")
                            print(f"   Pickup items: {summary.get('pickup_items', 0)}")
                            print(f"   Delivery items: {summary.get('delivery_items', 0)}")
                            
                            if cart_items:
                                print(f"\n   Recent items in cart:")
                                for item in cart_items[-5:]:  # Show last 5
                                    print(f"     - {item.get('product_id')} (qty: {item.get('quantity')})")
                        else:
                            print(f"⚠️  Response: {result_json}")
                    except json.JSONDecodeError:
                        print(f"Response: {result_text}")
            except Exception as e:
                print(f"⚠️  Error viewing cart: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE ✅")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(test_add_recipe_complete())
