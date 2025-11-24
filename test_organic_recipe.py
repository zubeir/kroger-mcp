#!/usr/bin/env python3
"""
Custom add_recipe_to_cart test with organic and favorite ingredients
"""

import sys
sys.path.insert(0, 'src')

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def test_organic_recipe():
    """Test add_recipe_to_cart with organic and favorite ingredients"""
    
    print("=" * 70)
    print("ORGANIC & FAVORITES RECIPE TEST: add_recipe_to_cart")
    print("=" * 70)
    
    # Custom recipe with favorite and organic ingredients
    recipe_name = "Homemade Organic Granola with Berries"
    
    # Your favorite organic ingredients
    ingredients = [
        "organic rolled oats",
        "organic honey",
        "organic almond butter",
        "organic coconut oil",
        "organic blueberries",
        "organic almonds",
        "organic chia seeds",
        "organic sea salt",
        "organic vanilla extract",
        "organic cinnamon"
    ]
    
    print("\nRecipe: {}".format(recipe_name))
    print("Ingredients ({} items):".format(len(ingredients)))
    for ing in ingredients:
        print("  - {}".format(ing))
    print()
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=['run_server.py'],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[OK] Connected to MCP server\n")
            
            # Step 1: Find locations near zip code
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
                            print("[OK] Found: {}".format(name))
                            print("     Location ID: {}\n".format(location_id))
                    except json.JSONDecodeError as e:
                        print("[ERROR] Could not parse location response\n")
            except Exception as e:
                print("[ERROR] Error searching locations: {}\n".format(str(e)))
            
            if not location_id:
                print("[ERROR] Could not find a store location. Exiting.\n")
                return
            
            # Step 2: Get the prompt
            print("Step 2: Getting the add_recipe_to_cart prompt")
            print("-" * 70)
            try:
                result = await session.get_prompt(
                    'add_recipe_to_cart', 
                    arguments={'recipe_type': recipe_name}
                )
                
                if result.messages:
                    prompt_text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                    print("[OK] Prompt generated successfully\n")
                    print("Prompt text:\n{}".format(prompt_text))
                    print()
            except Exception as e:
                print("[ERROR] Error getting prompt: {}\n".format(str(e)))
                return
            
            # Step 3: Search for products
            print("Step 3: Searching for organic ingredients at location {}".format(location_id))
            print("-" * 70)
            
            found_products = []
            not_found = []
            
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
                                
                                # Get pricing
                                price_str = "N/A"
                                if product.get('items'):
                                    item = product['items'][0]
                                    if item.get('price'):
                                        price_data = item['price']
                                        regular = price_data.get('regular')
                                        sale = price_data.get('promo')
                                        if sale:
                                            price_str = "${:.2f}".format(sale)
                                        elif regular:
                                            price_str = "${:.2f}".format(regular)
                                
                                print("[OK] {:<30s} -> {:<50s}".format(ing, desc[:50]))
                                found_products.append({
                                    "ingredient": ing,
                                    "product_id": pid,
                                    "description": desc,
                                    "price": price_str
                                })
                            else:
                                print("[..] {:<30s} -> No products found".format(ing))
                                not_found.append(ing)
                        except json.JSONDecodeError:
                            print("[..] {:<30s} -> Could not parse response".format(ing))
                            not_found.append(ing)
                    else:
                        print("[..] {:<30s} -> No search result".format(ing))
                        not_found.append(ing)
                        
                except Exception as e:
                    print("[ERROR] {:<30s} -> Error: {}".format(ing, str(e)[:50]))
                    not_found.append(ing)
            
            print()
            print("Search Results Summary:")
            print("  Found: {} items".format(len(found_products)))
            print("  Not found: {} items".format(len(not_found)))
            if not_found:
                print("  Missing: {}".format(", ".join(not_found)))
            print()
            
            # Step 4: Add to cart
            if found_products:
                print("Step 4: Adding {} item(s) to cart".format(len(found_products)))
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
                                print("[OK] Successfully added {} item(s) to cart!".format(result_json.get('items_added', len(found_products))))
                            else:
                                error_msg = result_json.get("error", "Unknown error")
                                print("[..] Add failed: {}".format(error_msg[:100]))
                        except json.JSONDecodeError:
                            print("[..] Response: {}".format(result_text[:200]))
                    else:
                        print("[..] No response from bulk_add_to_cart")
                        
                except Exception as e:
                    print("[ERROR] Error adding to cart: {}".format(str(e)))
                    
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
                            
                            print("[OK] FINAL CART STATUS:")
                            print("     ===================================")
                            print("     Total items in cart: {}".format(summary.get('total_items', 0)))
                            print("     Total quantity: {}".format(summary.get('total_quantity', 0)))
                            print("     Pickup items: {}".format(summary.get('pickup_items', 0)))
                            print("     Delivery items: {}".format(summary.get('delivery_items', 0)))
                            print("     Last updated: {}".format(summary.get('last_updated', 'N/A')))
                            print("     ===================================")
                            
                            if cart_items:
                                print("\n     Items added in this session:")
                                added_in_session = 0
                                for item in cart_items[-len(found_products):] if found_products else []:
                                    ing_name = None
                                    for p in found_products:
                                        if p["product_id"] == item.get('product_id'):
                                            ing_name = p["ingredient"]
                                            break
                                    if ing_name:
                                        print("       [+] {} (qty: {})".format(ing_name, item.get('quantity')))
                                        added_in_session += 1
                                if added_in_session == 0 and found_products:
                                    print("       (Could not match items - {} new items may be in cart)".format(len(found_products)))
                        else:
                            print("[..] Response: {}".format(str(result_json)))
                    except json.JSONDecodeError:
                        print("[..] Response: {}".format(result_text))
            except Exception as e:
                print("[ERROR] Error viewing cart: {}".format(str(e)))
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE [OK]")
    print("=" * 70)
    print("\nRECIPE SUMMARY:")
    print("  Recipe: {}".format(recipe_name))
    print("  Total ingredients: {}".format(len(ingredients)))
    print("  Found at Kroger: {} items".format(len(found_products)))
    print("  Success rate: {:.1f}%".format((len(found_products) / len(ingredients)) * 100 if ingredients else 0))

if __name__ == '__main__':
    asyncio.run(test_organic_recipe())
