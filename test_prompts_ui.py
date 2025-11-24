#!/usr/bin/env python3
"""
Streamlit UI for testing Kroger MCP Prompts

This creates a web-based UI to test all 4 Kroger MCP prompts.

Usage:
    streamlit run test_prompts_ui.py
"""

import os
import sys
import asyncio
import concurrent.futures
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import streamlit as st

# Add src to path to import kroger_mcp
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    try:
        from mcp.client import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        MCP_AVAILABLE = True
    except ImportError:
        MCP_AVAILABLE = False


# Page configuration
st.set_page_config(
    page_title="Kroger MCP Prompts Tester",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .prompt-card {
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin: 1rem 0;
        background-color: #f9f9f9;
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_server_script_path():
    """Get the path to run_server.py"""
    return Path(__file__).parent / "run_server.py"


async def get_prompts_from_server():
    """Connect to server and get list of prompts"""
    if not MCP_AVAILABLE:
        return None, "MCP SDK not available. Please install with: pip install mcp"
    
    server_script = get_server_script_path()
    if not server_script.exists():
        return None, f"Server script not found: {server_script}"
    
    try:
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(server_script)],
            env=os.environ.copy()
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                prompts_result = await session.list_prompts()
                return prompts_result.prompts, None
    except Exception as e:
        return None, str(e)


async def test_prompt(prompt_name: str, arguments: Dict[str, Any] = None, execute_actions: bool = True):
    """Test a specific prompt and optionally execute the actions"""
    if not MCP_AVAILABLE:
        return None, "MCP SDK not available"
    
    server_script = get_server_script_path()
    if not server_script.exists():
        return None, "Server script not found"
    
    try:
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(server_script)],
            env=os.environ.copy()
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                try:
                    await session.initialize()
                    
                    # Get the prompt text
                    if arguments:
                        result = await session.get_prompt(prompt_name, arguments=arguments)
                    else:
                        result = await session.get_prompt(prompt_name)
                    
                    if not result.messages or len(result.messages) == 0:
                        return None, "No content returned"
                    
                    prompt_text = result.messages[0].content.text if hasattr(result.messages[0].content, 'text') else str(result.messages[0].content)
                    
                    # If execute_actions is True, actually execute the actions described in the prompt
                    if execute_actions:
                        try:
                            execution_result = await execute_prompt_actions(session, prompt_name, arguments, prompt_text)
                            if execution_result:
                                return f"{prompt_text}\n\n{'='*60}\n\nEXECUTION RESULTS:\n\n{execution_result}", None
                        except Exception as exec_error:
                            # Catch errors during execution but still return the prompt text
                            error_msg = str(exec_error)[:200]
                            return f"{prompt_text}\n\n{'='*60}\n\nEXECUTION ERROR:\n\n❌ {error_msg}", None
                    
                    return prompt_text, None
                except Exception as session_error:
                    # Catch any errors in the session
                    error_msg = str(session_error)
                    if "TaskGroup" in error_msg:
                        return None, f"TaskGroup error: {error_msg[:200]}. This may indicate an issue with async operations. Try disabling 'Execute Actions'."
                    return None, f"Session error: {error_msg[:200]}"
    except Exception as e:
        error_msg = str(e)
        if "TaskGroup" in error_msg:
            return None, f"TaskGroup error: {error_msg[:200]}. This may indicate an issue with async operations."
        return None, f"Error: {error_msg[:200]}"


def normalize_ingredient_quantity(name: str, qty: float, unit: str) -> int:
    """
    Convert recipe unit quantities (cups, tbsp, tsp) to realistic grocery package counts.
    
    Examples:
    - 2 cups flour -> 1 (5lb bag covers)
    - 1 stick butter -> 1 (4-stick pack)
    - 6 eggs -> 1 (dozen carton)
    - 1 tbsp vanilla -> 1 (bottle)
    """
    name_lower = name.lower()
    
    # Spices/extracts: small amounts, 1 container is plenty
    if unit in ("tsp", "tbsp") and any(x in name_lower for x in ["cinnamon", "vanilla", "extract", "salt", "baking", "soda", "powder", "nutmeg", "ginger"]):
        return 1
    
    # Flour/sugar: 1-2 cups per recipe; 5lb bag ≈ 18-20 cups
    if unit == "cups" and any(x in name_lower for x in ["flour", "sugar", "brown sugar", "granulated"]):
        return max(1, int(qty / 3))  # conservative: 1 bag per 3 cups needed
    
    # Butter: 1 stick = 0.5 cups; 4-stick packs typical
    if "butter" in name_lower:
        if unit == "sticks":
            return max(1, int((qty + 3) // 4))  # round up to nearest 4-stick pack
        elif unit == "cups":
            sticks_needed = qty * 2  # 1 cup = 2 sticks
            return max(1, int((sticks_needed + 3) // 4))
        return 1
    
    # Eggs: typically 1 dozen per recipe
    if "egg" in name_lower or (unit == "count" and "egg" in name_lower):
        if unit == "count":
            return max(1, int((qty + 11) // 12))  # round up to nearest dozen
        return 1
    
    # Produce (apples, bananas, etc.): 1 bag/bunch covers most recipes
    if any(x in name_lower for x in ["apple", "banana", "tomato", "pepper", "lettuce", "onion", "garlic"]):
        return 1
    
    # Juices/extracts: 1 bottle per recipe
    if any(x in name_lower for x in ["juice", "lemon", "lime", "orange"]):
        return 1
    
    # Chocolate chips, nuts: 10-12 oz bags ≈ 1.5-2 cups; typical recipe uses 1-2 cups
    if any(x in name_lower for x in ["chocolate", "chip", "nut", "peanut", "walnut"]):
        if unit == "cups":
            return max(1, int((qty + 1) // 1.5))
        return 1
    
    # Default: 1 package
    return 1


async def execute_prompt_actions(session: ClientSession, prompt_name: str, arguments: Dict[str, Any], prompt_text: str):
    """Execute the actual actions described in the prompt"""
    results = []
    
    try:
        # Wrap in try-except to catch any TaskGroup errors
        if prompt_name == "grocery_list_store_path":
            # Extract grocery items from arguments
            grocery_list = arguments.get("grocery_list", "") if arguments else ""
            
            # Parse items from the list
        
            for line in grocery_list.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove dashes and bullets
                    item = line.lstrip('- •*').strip()
                    if item:
                        items.append(item)
            
            if not items:
                return "❌ No items found in grocery list"
            
            results.append(f"📋 Found {len(items)} items to search for:\n{chr(10).join(f'  - {item}' for item in items)}\n")
            
            # Get preferred location
            location_id = None
            try:
                location_result = await session.call_tool("get_preferred_location", {})
                if location_result and len(location_result.content) > 0:
                    location_data = location_result.content[0].text if hasattr(location_result.content[0], 'text') else str(location_result.content[0])
                    try:
                        location_json = json.loads(location_data)
                        location_id = location_json.get("location_id")
                    except (json.JSONDecodeError, KeyError, AttributeError) as e:
                        # Silently ignore parsing errors
                        pass
            except Exception as e:
                # Silently ignore if location can't be retrieved
                pass
            
            if not location_id:
                results.append("⚠️  No preferred location set. Searching products without location filter.\n")
            
            # Search for each product
            product_results = []
            for item in items[:10]:  # Limit to 10 items for performance
                try:
                    search_args = {"search_term": item, "limit": 3}
                    if location_id:
                        search_args["location_id"] = location_id
                    
                    search_result = await session.call_tool("search_products", search_args)
                    if search_result and len(search_result.content) > 0:
                        result_text = search_result.content[0].text if hasattr(search_result.content[0], 'text') else str(search_result.content[0])
                        try:
                            result_json = json.loads(result_text)
                            products = result_json.get("data", [])
                            if products:
                                product_results.append(f"  ✅ {item}: Found {len(products)} product(s)")
                                # Show first product details
                                first_product = products[0]
                                pricing = first_product.get('pricing', {})
                                price_str = pricing.get('formatted_regular', 'N/A') if pricing else 'N/A'
                                product_results.append(f"     → {first_product.get('description', 'N/A')} ({price_str})")
                            else:
                                product_results.append(f"  ⚠️  {item}: No products found")
                        except (json.JSONDecodeError, KeyError, AttributeError) as parse_error:
                            product_results.append(f"  ✅ {item}: Search completed (parse error: {str(parse_error)[:50]})")
                except Exception as e:
                    error_msg = str(e)[:100]  # Limit error message length
                    product_results.append(f"  ❌ {item}: Error - {error_msg}")
            
            if product_results:
                results.append("🔍 Product Search Results:\n" + "\n".join(product_results))
            else:
                results.append("⚠️  Could not search for products. Make sure a preferred location is set.")
        
        elif prompt_name == "pharmacy_open_check":
            # Get preferred location
            location_id = None
            try:
                location_result = await session.call_tool("get_preferred_location", {})
                if location_result and len(location_result.content) > 0:
                    location_data = location_result.content[0].text if hasattr(location_result.content[0], 'text') else str(location_result.content[0])
                    try:
                        location_json = json.loads(location_data)
                        location_id = location_json.get("location_id")
                    except (json.JSONDecodeError, KeyError, AttributeError):
                        pass
            except Exception as e:
                return f"❌ Error getting preferred location: {str(e)}"
            
            if not location_id:
                return "❌ No preferred location set. Please set a preferred location first using set_preferred_location."
            
            # Get location details
            try:
                details_result = await session.call_tool("get_location_details", {"location_id": location_id})
                if details_result and len(details_result.content) > 0:
                    details_text = details_result.content[0].text if hasattr(details_result.content[0], 'text') else str(details_result.content[0])
                    try:
                        details_json = json.loads(details_text)
                        departments = details_json.get("departments", [])
                        
                        pharmacy_dept = None
                        for dept in departments:
                            if dept.get("name", "").lower() == "pharmacy":
                                pharmacy_dept = dept
                                break
                        
                        if pharmacy_dept:
                            results.append("✅ Pharmacy found at this location!\n")
                            results.append(f"📋 Pharmacy Information:\n")
                            results.append(f"  Name: {pharmacy_dept.get('name', 'N/A')}")
                            
                            # Check hours
                            hours = pharmacy_dept.get("hours", {})
                            if hours:
                                results.append(f"\n  Hours:")
                                for day, time_range in hours.items():
                                    results.append(f"    {day}: {time_range}")
                            
                            # Services
                            services = pharmacy_dept.get("services", [])
                            if services:
                                results.append(f"\n  Services Available:")
                                for service in services:
                                    results.append(f"    - {service}")
                        else:
                            results.append("❌ No pharmacy found at this location.")
                    except (json.JSONDecodeError, KeyError, AttributeError) as parse_error:
                        results.append(f"⚠️  Could not parse location details: {str(parse_error)}")
            except Exception as e:
                results.append(f"❌ Error getting location details: {str(e)}")
        
        elif prompt_name == "set_preferred_store":
            zip_code = arguments.get("zip_code") if arguments else None
            if zip_code:
                try:
                    search_result = await session.call_tool("search_locations", {"zip_code": zip_code, "limit": 5})
                    if search_result and len(search_result.content) > 0:
                        result_text = search_result.content[0].text if hasattr(search_result.content[0], 'text') else str(search_result.content[0])
                        try:
                            result_json = json.loads(result_text)
                            locations = result_json.get("data", [])
                            if locations:
                                results.append(f"✅ Found {len(locations)} store(s) near zip code {zip_code}:\n")
                                for i, loc in enumerate(locations[:5], 1):
                                    results.append(f"\n{i}. {loc.get('name', 'N/A')}")
                                    results.append(f"   Address: {loc.get('address', {}).get('address_line1', 'N/A')}")
                                    results.append(f"   Distance: {loc.get('distance', {}).get('value', 'N/A')} {loc.get('distance', {}).get('unit', 'miles')}")
                                    results.append(f"   Location ID: {loc.get('location_id', 'N/A')}")
                            else:
                                results.append(f"⚠️  No stores found near zip code {zip_code}")
                        except (json.JSONDecodeError, KeyError, AttributeError) as parse_error:
                            results.append(f"✅ Location search completed (parse error: {str(parse_error)[:50]})")
                except Exception as e:
                    error_msg = str(e)[:100]
                    results.append(f"❌ Error searching locations: {error_msg}")
        
        elif prompt_name == "add_recipe_to_cart":
            recipe_type = arguments.get("recipe_type", "chocolate chip cookies") if arguments else "chocolate chip cookies"
            results.append(f"📝 Recipe type: {recipe_type}\n")

            # Define recipes with (ingredient_name, qty, unit) tuples
            recipes = {
                "apple pie": [
                    ("apples", 6, "count"),
                    ("all-purpose flour", 2, "cups"),
                    ("granulated sugar", 1, "cups"),
                    ("butter", 1, "sticks"),
                    ("salt", 0.25, "tsp"),
                    ("ground cinnamon", 1, "tsp"),
                    ("lemon juice", 1, "tbsp"),
                    ("eggs", 1, "count")
                ],
                "chocolate chip cookies": [
                    ("all-purpose flour", 2.25, "cups"),
                    ("granulated sugar", 0.75, "cups"),
                    ("brown sugar", 0.75, "cups"),
                    ("butter", 1, "sticks"),
                    ("eggs", 2, "count"),
                    ("vanilla extract", 1, "tsp"),
                    ("baking soda", 1, "tsp"),
                    ("salt", 0.5, "tsp"),
                    ("chocolate chips", 2, "cups")
                ],
                "brownies": [
                    ("all-purpose flour", 0.75, "cups"),
                    ("granulated sugar", 1.5, "cups"),
                    ("butter", 0.5, "sticks"),
                    ("cocoa powder", 0.75, "cups"),
                    ("eggs", 2, "count"),
                    ("vanilla extract", 1, "tsp"),
                    ("salt", 0.25, "tsp"),
                    ("baking powder", 0.5, "tsp")
                ]
            }
            
            # Match recipe by name (case-insensitive substring match)
            recipe_name = recipe_type.lower()
            matched_recipe = None
            for recipe_key, ingredients in recipes.items():
                if recipe_key in recipe_name or recipe_name in recipe_key:
                    matched_recipe = ingredients
                    break
            
            if not matched_recipe:
                # Use chocolate chip cookies as default
                matched_recipe = recipes["chocolate chip cookies"]
                results.append(f"⚠️  Recipe '{recipe_type}' not found; using chocolate chip cookies as default.\n")

            results.append(f"📋 Recipe ingredients ({len(matched_recipe)} items):\n")
            for ing_name, ing_qty, ing_unit in matched_recipe:
                results.append(f"  - {ing_name}: {ing_qty} {ing_unit}")
            results.append("")

            # Normalize quantities to package counts
            normalized_ingredients = [
                (ing_name, normalize_ingredient_quantity(ing_name, ing_qty, ing_unit))
                for ing_name, ing_qty, ing_unit in matched_recipe
            ]
            
            results.append(f"📦 Normalized to grocery packages:\n")
            for ing_name, pkg_count in normalized_ingredients:
                results.append(f"  - {ing_name}: {pkg_count} package(s)")
            results.append("")

            # Resolve location: use zip_code or preferred location
            zip_code = arguments.get("zip_code") if arguments else None
            modality = arguments.get("modality", "PICKUP") if arguments else "PICKUP"
            
            location_id = None
            if zip_code:
                try:
                    loc_res = await session.call_tool("search_locations", {"zip_code": zip_code, "limit": 1})
                    if loc_res and len(loc_res.content) > 0:
                        loc_text = loc_res.content[0].text if hasattr(loc_res.content[0], 'text') else str(loc_res.content[0])
                        try:
                            loc_json = json.loads(loc_text)
                            locs = loc_json.get('data', [])
                            if locs:
                                location_id = locs[0].get('locationId') or locs[0].get('location_id')
                        except Exception:
                            pass
                except Exception:
                    pass

            if not location_id:
                try:
                    pref = await session.call_tool("get_preferred_location", {})
                    if pref and len(pref.content) > 0:
                        pref_text = pref.content[0].text if hasattr(pref.content[0], 'text') else str(pref.content[0])
                        try:
                            pj = json.loads(pref_text)
                            location_id = pj.get('location_id') or pj.get('locationId')
                        except Exception:
                            pass
                except Exception:
                    pass

            if not location_id:
                results.append("❌ Could not resolve store location. Provide a zip code or set a preferred location.")
                return "\n".join(results)

            results.append(f"🏪 Resolved store location: {location_id}\n")
            results.append("🔍 Searching Kroger for ingredients...\n")

            # Search for each ingredient and add to cart
            added = []
            not_found = []
            total = 0.0

            for ing_name, pkg_qty in normalized_ingredients:
                try:
                    search_args = {"search_term": ing_name, "location_id": location_id, "limit": 2}
                    search_res = await session.call_tool("search_products", search_args)
                    if not search_res or len(search_res.content) == 0:
                        not_found.append(ing_name)
                        continue
                    
                    text = search_res.content[0].text if hasattr(search_res.content[0], 'text') else str(search_res.content[0])
                    try:
                        j = json.loads(text)
                    except Exception:
                        not_found.append(ing_name)
                        continue
                    
                    data = j.get('data', [])
                    if not data:
                        not_found.append(ing_name)
                        continue
                    
                    product = data[0]
                    pid = product.get('productId')
                    desc = product.get('description')
                    item = (product.get('items') or [None])[0]
                    price_val = None
                    
                    if item and item.get('price'):
                        price = item['price']
                        # Use promo price if available (sale), otherwise regular
                        if price.get('promo') is not None:
                            price_val = float(price.get('promo'))
                        elif price.get('regular') is not None:
                            price_val = float(price.get('regular'))
                    
                    if price_val is None:
                        not_found.append(ing_name)
                        continue
                    
                    # Add to local cart via bulk_add_to_cart
                    await session.call_tool("bulk_add_to_cart", {
                        "items": [{
                            "product_id": pid,
                            "quantity": pkg_qty,
                            "modality": modality
                        }]
                    })
                    
                    subtotal = round(price_val * pkg_qty, 2)
                    added.append({
                        "ingredient": ing_name,
                        "product": desc,
                        "unit_price": price_val,
                        "quantity": pkg_qty,
                        "subtotal": subtotal
                    })
                    total += subtotal
                except Exception as e:
                    not_found.append(ing_name)

            # Output summary
            results.append("✅ Items Added to Cart:\n")
            if added:
                for item in added:
                    results.append(f"  • {item['ingredient']}")
                    results.append(f"    → {item['product']}")
                    results.append(f"    → qty: {item['quantity']} × ${item['unit_price']:.2f} = ${item['subtotal']:.2f}")
                results.append(f"\n💰 TOTAL COST (estimated): ${total:.2f}")
            else:
                results.append("  (No items found)")
            
            if not_found:
                results.append(f"\n⚠️ Items NOT FOUND: {', '.join(not_found)}")

            return "\n".join(results)
        
        elif prompt_name == "find_items_on_sale":
            category = arguments.get("category") if arguments else None
            # Convert limit from string to int for processing
            limit_str = arguments.get("limit", "20") if arguments else "20"
            try:
                limit = int(limit_str)
                if limit < 1:
                    limit = 1
                elif limit > 50:
                    limit = 50
            except (ValueError, TypeError):
                limit = 20
            
            # Get preferred location
            location_id = None
            try:
                location_result = await session.call_tool("get_preferred_location", {})
                if location_result and len(location_result.content) > 0:
                    location_data = location_result.content[0].text if hasattr(location_result.content[0], 'text') else str(location_result.content[0])
                    try:
                        location_json = json.loads(location_data)
                        location_id = location_json.get("location_id")
                    except (json.JSONDecodeError, KeyError, AttributeError):
                        pass
            except Exception as e:
                return f"❌ Error getting preferred location: {str(e)}"
            
            if not location_id:
                return "❌ No preferred location set. Please set a preferred location first using set_preferred_location."
            
            # Search for products (use category if provided, otherwise search common terms)
            search_terms = [category] if category else ["sale", "promo", "discount", "special"]
            sale_items = []
            
            for search_term in search_terms[:3]:  # Limit searches
                try:
                    search_args = {"search_term": search_term, "limit": 50, "location_id": location_id}
                    search_result = await session.call_tool("search_products", search_args)
                    if search_result and len(search_result.content) > 0:
                        result_text = search_result.content[0].text if hasattr(search_result.content[0], 'text') else str(search_result.content[0])
                        try:
                            result_json = json.loads(result_text)
                            products = result_json.get("data", [])
                            
                            # Filter for items on sale
                            for product in products:
                                try:
                                    pricing = product.get("pricing", {})
                                    if pricing and pricing.get("on_sale", False):
                                        regular = pricing.get("regular_price", 0) or 0
                                        sale = pricing.get("sale_price", 0) or 0
                                        if regular > 0 and sale < regular:
                                            savings = regular - sale
                                            discount_pct = (savings / regular * 100) if regular > 0 else 0
                                            
                                            aisle_locations = product.get("aisle_locations", [])
                                            aisle = aisle_locations[0].get("description", "N/A") if aisle_locations and len(aisle_locations) > 0 else "N/A"
                                            
                                            sale_items.append({
                                                "description": product.get("description", "N/A"),
                                                "brand": product.get("brand", ""),
                                                "regular_price": regular,
                                                "sale_price": sale,
                                                "savings": savings,
                                                "discount_pct": discount_pct,
                                                "aisle": aisle
                                            })
                                except (KeyError, TypeError, AttributeError) as item_error:
                                    # Skip items with invalid pricing data
                                    continue
                        except (json.JSONDecodeError, KeyError, AttributeError) as parse_error:
                            # Skip this search result if parsing fails
                            continue
                except Exception as e:
                    error_msg = str(e)[:100]
                    results.append(f"⚠️  Error searching for '{search_term}': {error_msg}")
            
            # Sort by savings (highest first) and limit
            sale_items.sort(key=lambda x: x.get("savings", 0), reverse=True)
            sale_items = sale_items[:limit]
            
            if sale_items:
                results.append(f"✅ Found {len(sale_items)} item(s) on sale:\n")
                for i, item in enumerate(sale_items, 1):
                    try:
                        results.append(f"\n{i}. {item.get('brand', '')} {item.get('description', 'N/A')}")
                        results.append(f"   Regular Price: ${item.get('regular_price', 0):.2f}")
                        results.append(f"   Sale Price: ${item.get('sale_price', 0):.2f}")
                        results.append(f"   You Save: ${item.get('savings', 0):.2f} ({item.get('discount_pct', 0):.1f}% off)")
                        if item.get('aisle') != "N/A":
                            results.append(f"   Aisle: {item.get('aisle')}")
                    except (KeyError, TypeError) as format_error:
                        # Skip items with formatting issues
                        continue
            else:
                results.append("⚠️  No sale items found. Try searching different categories or terms.")
        
        return "\n".join(results) if results else None
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        # Limit error message to avoid overwhelming the UI
        error_msg = str(e)[:200]
        return f"❌ Error executing actions: {error_msg}\n\nDetails: {error_details[:500]}"


def run_async(coro):
    """Run async function in Streamlit"""
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create a new one in a thread
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(coro)


def main():
    """Main UI"""
    # Header
    st.markdown('<div class="main-header">🛒 Kroger MCP Prompts Tester</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Navigation")
        page = st.radio(
            "Select Page",
            ["Test Prompts", "About"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        st.header("ℹ️ Info")
        if MCP_AVAILABLE:
            st.success("✅ MCP SDK Available")
        else:
            st.error("❌ MCP SDK Not Available")
            st.info("Install with: `pip install mcp`")
        
        server_script = get_server_script_path()
        if server_script.exists():
            st.success(f"✅ Server script found")
        else:
            st.error(f"❌ Server script not found")
    
    if page == "About":
        st.header("About")
        st.markdown("""
        ### Kroger MCP Prompts Tester
        
        This web UI allows you to test all 4 Kroger MCP prompts:
        
        1. **grocery_list_store_path** - Optimize shopping path through store
        2. **pharmacy_open_check** - Check if pharmacy is open
        3. **set_preferred_store** - Set preferred Kroger store
        4. **add_recipe_to_cart** - Find recipe and add ingredients to cart
        
        ### Usage
        
        1. Select a prompt from the dropdown
        2. Fill in any required parameters
        3. Click "Test Prompt" to see the result
        
        ### Requirements
        
        - MCP SDK: `pip install mcp`
        - Streamlit: `pip install streamlit`
        - Server script: `run_server.py` must exist
        """)
        return
    
    # Main content - Test Prompts
    st.header("🧪 Test Prompts")
    
    # Check prerequisites
    if not MCP_AVAILABLE:
        st.error("❌ MCP SDK not available. Please install with: `pip install mcp`")
        st.stop()
    
    server_script = get_server_script_path()
    if not server_script.exists():
        st.error(f"❌ Server script not found: {server_script}")
        st.stop()
    
    # Get available prompts
    with st.spinner("Connecting to server and loading prompts..."):
        prompts, error = run_async(get_prompts_from_server())
    
    if error:
        st.error(f"❌ Error connecting to server: {error}")
        st.info("💡 Make sure the server can be started. The UI will start it automatically.")
        st.stop()
    
    if not prompts:
        st.warning("⚠️ No prompts found on the server")
        st.stop()
    
    # Prompt selection
    prompt_names = [p.name for p in prompts]
    prompt_info = {p.name: p for p in prompts}
    
    selected_prompt = st.selectbox(
        "Select Prompt to Test",
        prompt_names,
        help="Choose which prompt you want to test"
    )
    
    if selected_prompt:
        prompt = prompt_info[selected_prompt]
        
        # Display prompt info
        with st.expander("📝 Prompt Information", expanded=False):
            st.write(f"**Name:** {prompt.name}")
            if prompt.description:
                st.write(f"**Description:** {prompt.description}")
            if prompt.arguments:
                st.write("**Arguments:**")
                # Handle arguments as either dict or list
                if isinstance(prompt.arguments, dict):
                    for arg_name, arg_info in prompt.arguments.items():
                        desc = arg_info.get('description', 'No description') if isinstance(arg_info, dict) else str(arg_info)
                        st.write(f"  - `{arg_name}`: {desc}")
                elif isinstance(prompt.arguments, list):
                    for arg in prompt.arguments:
                        if isinstance(arg, dict):
                            arg_name = arg.get('name', 'Unknown')
                            arg_desc = arg.get('description', 'No description')
                            arg_type = arg.get('type', '')
                            type_str = f" ({arg_type})" if arg_type else ""
                            st.write(f"  - `{arg_name}`{type_str}: {arg_desc}")
                        else:
                            st.write(f"  - {arg}")
                else:
                    st.write(f"  - {prompt.arguments}")
        
        # Input form based on prompt
        st.divider()
        st.subheader("📥 Input Parameters")
        
        arguments = {}
        
        if selected_prompt == "grocery_list_store_path":
            grocery_list = st.text_area(
                "Grocery List",
                value="""- Milk
- Bread
- Eggs
- Chicken breast
- Tomatoes
- Lettuce
- Bananas""",
                help="Enter your grocery list (one item per line, with or without dashes)",
                height=150
            )
            arguments["grocery_list"] = grocery_list
            
        elif selected_prompt == "pharmacy_open_check":
            st.info("ℹ️ This prompt doesn't require any parameters.")
            
        elif selected_prompt == "set_preferred_store":
            zip_code = st.text_input(
                "Zip Code",
                value="45202",
                help="Enter the zip code to search for stores near"
            )
            if zip_code:
                arguments["zip_code"] = zip_code
                
        elif selected_prompt == "add_recipe_to_cart":
            recipe_type = st.text_input(
                "Recipe Type",
                value="chocolate chip cookies",
                help="Enter the type of recipe you want to make"
            )
            # Ensure recipe_type is always provided (it's required by the prompt)
            arguments["recipe_type"] = recipe_type if recipe_type else "chocolate chip cookies"
            
            st.write("")
            st.info("Optional: Provide an ingredient list to test product lookup and adding to cart")
            ingredient_list = st.text_area(
                "Ingredient List (optional)",
                value="",
                help="Paste a list of ingredients (one per line). If provided, the UI will search Kroger for each ingredient and attempt to add matching items to the cart."
            )
            if ingredient_list:
                arguments["ingredient_list"] = ingredient_list

            modality = st.selectbox(
                "Fulfillment Modality",
                ["PICKUP", "DELIVERY"],
                index=0,
                help="Select whether items should be added for pickup or delivery"
            )
            arguments["modality"] = modality
        
        elif selected_prompt == "find_items_on_sale":
            col1, col2 = st.columns(2)
            with col1:
                category = st.text_input(
                    "Category (Optional)",
                    value="",
                    help="Filter by category (e.g., 'dairy', 'produce', 'meat', 'bakery'). Leave empty to search all categories."
                )
                if category:
                    arguments["category"] = category
            with col2:
                limit = st.number_input(
                    "Max Results",
                    min_value=1,
                    max_value=50,
                    value=20,
                    help="Maximum number of sale items to return (1-50)"
                )
                # Convert to string for MCP protocol compatibility
                arguments["limit"] = str(limit)
        
        # Test options
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            execute_actions = st.checkbox(
                "Execute Actions",
                value=True,
                help="If checked, will actually execute the actions described in the prompt (e.g., search for products, check pharmacy status). If unchecked, only returns the prompt text."
            )
        with col2:
            st.write("")  # Spacer
        
        # Test button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            test_button = st.button("🚀 Test Prompt", type="primary", use_container_width=True)
        
        # Execute test
        if test_button:
            spinner_text = "Testing prompt..." + (" and executing actions..." if execute_actions else "...")
            with st.spinner(spinner_text):
                # Always pass arguments dict (even if empty) to preserve any populated values
                result, error = run_async(test_prompt(selected_prompt, arguments, execute_actions=execute_actions))
            
            st.divider()
            st.subheader("📤 Result")
            
            if error:
                st.markdown(f'<div class="error-box">❌ <strong>Error:</strong> {error}</div>', unsafe_allow_html=True)
            elif result:
                st.markdown(f'<div class="success-box">✅ <strong>Success!</strong> Prompt generated successfully.</div>', unsafe_allow_html=True)
                st.text_area(
                    "Generated Prompt",
                    value=result,
                    height=300,
                    label_visibility="collapsed"
                )
                
                # Download button
                st.download_button(
                    label="📥 Download Result",
                    data=result,
                    file_name=f"{selected_prompt}_result.txt",
                    mime="text/plain"
                )
            else:
                st.warning("⚠️ No result returned")


if __name__ == "__main__":
    main()

