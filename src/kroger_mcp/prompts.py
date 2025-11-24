"""
MCP prompts for the Kroger MCP server
"""

from typing import List, Dict, Any, Optional
from fastmcp import Context
from pydantic import Field


def register_prompts(mcp):
    """Register prompts with the FastMCP server"""
    
    @mcp.prompt()
    async def grocery_list_store_path(
        grocery_list: str = Field(
            ...,
            description="A list of grocery items the user wants to purchase. Can be formatted as a bulleted list or plain text, one item per line.",
            examples=["- Milk\n- Bread\n- Eggs", "Milk, Bread, Eggs, Chicken breast"]
        ),
        ctx: Context = None
    ) -> str:
        """
        Generate a prompt asking for the optimal path through a store based on a grocery list.
        
        This prompt helps users organize their shopping trip by finding the most efficient
        route through the store based on the items they need to purchase.
        
        Args:
            grocery_list: A list of grocery items the user wants to purchase
            
        Returns:
            A prompt asking for the optimal shopping path
        """
        return f"""I'm planning to go grocery shopping at Kroger with this list:

{grocery_list}

Can you help me find the most efficient path through the store? Please search for these products to determine their aisle locations, then arrange them in a logical shopping order. 

If you can't find exact matches for items, please suggest similar products that are available.

IMPORTANT: Please only organize my shopping path - DO NOT add any items to my cart.
"""

    @mcp.prompt()
    async def pharmacy_open_check(ctx: Context = None) -> str:
        """
        Generate a prompt asking whether a pharmacy at the preferred Kroger location is open.
        
        This prompt checks the pharmacy status at the user's preferred Kroger store location,
        including hours, services, and current availability.
        
        Returns:
            A prompt asking about pharmacy status
        """
        return """Can you tell me if the pharmacy at my preferred Kroger store is currently open? 

Please check the department information for the pharmacy department and let me know:
1. If there is a pharmacy at my preferred store
2. If it's currently open 
3. What the hours are for today
4. What services are available at this pharmacy

Please use the get_location_details tool to find this information for my preferred location.
"""

    @mcp.prompt()
    async def set_preferred_store(
        zip_code: Optional[str] = Field(
            None,
            description="The zip code to search for nearby Kroger stores. If not provided, uses the default zip code from environment variables.",
            examples=["45202", "90210", "10001"]
        ),
        ctx: Context = None
    ) -> str:
        """
        Generate a prompt to help the user set their preferred Kroger store.
        
        This prompt helps users find and select their preferred Kroger store location
        by searching for stores near a specified zip code.
        
        Args:
            zip_code: Optional zip code to search near
            
        Returns:
            A prompt asking for help setting a preferred store
        """
        zip_phrase = f" near zip code {zip_code}" if zip_code else ""
        
        return f"""I'd like to set my preferred Kroger store{zip_phrase}. Can you help me with this process?

Please:
1. Search for nearby Kroger stores{zip_phrase}
2. Show me a list of the closest options with their addresses
3. Let me choose one from the list
4. Set that as my preferred location 

For each store, please show the full address, distance, and any special features or departments.
"""

    @mcp.prompt()
    async def add_recipe_to_cart(
        recipe_type: str = Field(
            ...,
            description="The type of recipe to search for and add ingredients to cart. Can be any dish, dessert, or meal type.",
            examples=["chocolate chip cookies", "chicken curry", "vegetarian lasagna", "beef stir fry", "pasta carbonara"]
        ),
        ctx: Context = None
    ) -> str:
        """
        Generate a prompt to find a specific recipe and add ingredients to cart.
        
        This prompt helps users find a recipe online, extract the ingredients,
        search for those ingredients at Kroger, and add them to the shopping cart.
        
        Args:
            recipe_type: The type of recipe to search for (e.g., "chicken curry", "vegetarian lasagna")
            
        Returns:
            A prompt asking for a recipe and to add ingredients to cart
        """
        return f"""I'd like to make a recipe: {recipe_type}. Can you help me with the following:

1. Search the web for a good {recipe_type} recipe
2. Present the recipe with ingredients and instructions
3. Look up each ingredient in my local Kroger store
4. Add all the ingredients I'll need to my cart using bulk_add_to_cart
5. If any ingredients aren't available, suggest alternatives

Before adding items to cart, please ask me if I prefer pickup or delivery for these items.
"""

    @mcp.prompt()
    async def find_items_on_sale(
        category: Optional[str] = Field(
            None,
            description="Optional category to search for sale items (e.g., 'dairy', 'produce', 'meat', 'bakery'). If not provided, searches across all categories.",
            examples=["dairy", "produce", "meat", "bakery", "frozen", "beverages"]
        ),
        zip_code: Optional[str] = Field(
            "45202",
            description="The zip code to search for nearby Kroger stores. If not provided, uses 45202 as the default preferred store.",
            examples=["45202", "90210", "10001"]
        ),
        limit: str = Field(
            "20",
            description="Maximum number of sale items to return (1-50). Default is 20. Should be provided as a string."
        ),
        ctx: Context = None
    ) -> str:
        """
        Generate a prompt to find all items currently on sale at Kroger.
        
        This prompt helps users discover products that are currently on sale at their
        preferred Kroger store, showing regular prices, sale prices, and savings amounts.
        
        Args:
            category: Optional category to filter sale items (e.g., 'dairy', 'produce')
            limit: Maximum number of sale items to return (1-50)
            
        Returns:
            A prompt asking to find and display items on sale
        """
        category_phrase = f" in the {category} category" if category else ""
        
        # Convert limit to int for validation and display
        try:
            limit_int = int(limit) if limit else 20
            if limit_int < 1:
                limit_int = 1
            elif limit_int > 50:
                limit_int = 50
        except (ValueError, TypeError):
            limit_int = 20
        
        return f"""I need you to retrieve a complete list of ALL items currently on sale at the Kroger store located in zip code 45202.

Here's how to do this:

STEP 1: Search for products on sale using the search_products tool
- Use zip_code: "45202" parameter
- The tool will automatically look up the location for this zip code
- Search for common sale items or broad categories to find all items on sale
- Make multiple searches if needed to capture products{category_phrase if category_phrase else " across all categories"}
- Set limit to {limit_int} for each search

STEP 2: Filter and format the results
For each item on sale, provide the following information:
1. Product name and description
2. Original/Regular price (the normal price before any discount)
3. Sale price (the current discounted price)
4. Discount amount (the difference between original and sale price)
5. Discount percentage (calculated as: (discount amount / original price) * 100)
6. Aisle location (if available)

Output format for each item:
Product: [name and description]
Original Price: $[regular price]
Sale Price: $[sale price]
Discount: $[discount amount] ([discount percentage]% off)
Location: [aisle info if available]

Search instructions:
- Use the search_products tool with zip_code: "45202"
- The tool accepts both location_id and zip_code parameters
- If you provide zip_code, it will automatically find the location
- Include{category_phrase if category_phrase else " all categories"}
- Return up to {limit_int} items per search

Important requirements:
- Every item shown MUST have a sale price lower than the original price
- All prices and discounts must be clearly labeled and calculated correctly
- Results must be sorted by discount amount (highest to lowest) so the best deals appear first
- Do NOT set a preferred location - just use the zip_code parameter in search_products
"""

    @mcp.prompt()
    async def get_sale_items_45202(
        limit: str = Field(
            "50",
            description="Maximum number of sale items to return (1-200). Default is 50. Should be provided as a string."
        ),
        ctx: Context = None
    ) -> str:
        """
        Get a list of all items currently on sale at the Kroger store in zip code 45202.
        
        This prompt retrieves all items on sale at the specific store location and provides
        the original price, sale price, and discount for each item.
        
        Args:
            limit: Maximum number of sale items to return
            
        Returns:
            A prompt asking to retrieve sale items with pricing details
        """
        # Convert limit to int for validation
        try:
            limit_int = int(limit) if limit else 50
            if limit_int < 1:
                limit_int = 1
            elif limit_int > 200:
                limit_int = 200
        except (ValueError, TypeError):
            limit_int = 50
        
        return f"""I need you to search for and compile a comprehensive list of items currently on sale at the Kroger store identified by location_id 01400441.

    CRITICAL: Please perform multiple searches using different product names and terms. Search for POPULAR ITEMS that people commonly buy.

    Search Instructions:
    Use the `search_products` tool with `location_id: "01400441"` and search for these specific products and categories (run each search against the same location_id):

    Popular Items to Search:
    1. milk
    2. bread
    3. eggs
    4. chicken breast
    5. ground beef
    6. cheese
    7. yogurt
    8. butter
    9. apples
    10. bananas
    11. lettuce
    12. tomatoes
    13. peppers
    14. rice
    15. pasta
    16. canned vegetables
    17. cereal
    18. peanut butter
    19. coffee
    20. orange juice
    21. soda
    22. beer
    23. wine
    24. frozen pizza
    25. ice cream
    26. soup
    27. beans
    28. chips
    29. cookies
    30. chocolate

    IMPORTANT: For each search:
    - Use `search_products` with `location_id: "01400441"`
    - Set limit to {limit_int // 30 + 1} for each search (to get comprehensive results)
    - Look for items where the `sale_price` (promo) is LOWER than `regular_price`

COLLECTION PROCESS:
1. Go through each product name listed above
2. Execute the search_products tool for EACH one
3. From EACH search result, extract items that have:
   - regular_price (Original Price)
   - sale_price/promo (Sale Price) that is LESS than regular_price
   - Calculate: Discount Amount = regular_price - sale_price
   - Calculate: Discount % = (Discount Amount / regular_price) * 100

OUTPUT FORMAT - For each item on sale, show exactly this format:

Product: [product name and description]
Original Price: $[regular price formatted as XX.XX]
Sale Price: $[sale price formatted as XX.XX]
Discount: $[discount amount] ([discount percentage rounded to 1 decimal]% off)
Location: [aisle info if available, or "Not specified"]

THEN at the end, provide a SUMMARY showing:
- Total number of items found on sale
- Average discount percentage
- Highest discount item (name and discount %)
- Lowest price item (name and price)

CRITICAL REQUIREMENTS:
- SEARCH FOR ALL 30+ PRODUCT TYPES above
- Only show items where sale_price < regular_price
- Sort results by discount amount (highest to lowest)
- Include ALL items found (up to {limit_int} total)
- Do NOT skip any searches
- Be thorough and exhaustive in your search"""
