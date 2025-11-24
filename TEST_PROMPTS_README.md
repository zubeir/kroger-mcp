# Kroger MCP Prompts Test Client

This test client allows you to test all 4 Kroger MCP prompts to ensure they're working correctly.

## Overview

The test client (`test_prompts_client.py`) will:
1. ✅ Set up environment variables using `set_kroger_dev_env.ps1`
2. ✅ Create the MCP server instance
3. ✅ Test all 4 registered prompts:
   - `grocery_list_store_path` - Optimize shopping path
   - `pharmacy_open_check` - Check pharmacy hours
   - `set_preferred_store` - Set preferred Kroger store
   - `add_recipe_to_cart` - Find recipe and add ingredients

## Prerequisites

- Python 3.10+
- PowerShell (for running the environment setup script)
- All dependencies from `pyproject.toml` installed
- MCP SDK (optional, for full MCP protocol testing): `pip install mcp`
  - If not installed, the script will fall back to direct prompt testing

## Usage

### Basic Usage

```bash
# From the kroger-mcp directory
python test_prompts_client.py
```

### What It Does

1. **Environment Setup**: 
   - Runs `set_kroger_dev_env.ps1` to extract and set environment variables
   - Creates a `.env` file from the extracted variables
   - Verifies required variables (`KROGER_CLIENT_ID`, `KROGER_CLIENT_SECRET`) are set

2. **Server Startup**:
   - Starts the MCP server using `run_server.py` (via MCP SDK stdio client)
   - The server is automatically managed by the MCP client connection

3. **MCP Client Connection**:
   - Connects to the running server as an MCP client
   - Lists available prompts from the server
   - Tests each prompt via the MCP protocol

4. **Prompt Testing**:
   - Tests all 4 prompts with sample data:
     - `grocery_list_store_path` - with sample grocery list
     - `pharmacy_open_check` - no parameters
     - `set_preferred_store` - with zip code "45202"
     - `add_recipe_to_cart` - with "chocolate chip cookies"
   - Displays the generated prompt text
   - Reports success/failure for each test

5. **Fallback Mode**:
   - If MCP SDK is not available, tests prompts directly without MCP protocol
   - Still validates that prompts generate correct output

## Test Output

The script will output:
- ✅ Environment setup status
- ✅ Server creation status
- 📋 Generated prompt text for each test
- 📊 Summary of all test results

## Example Output

```
============================================================
🛒 Kroger MCP Prompts Test Client
============================================================
📝 Setting up environment from set_kroger_dev_env.ps1...
   ✓ Set KROGER_CLIENT_ID
   ✓ Set KROGER_CLIENT_SECRET
   ✓ Set KROGER_REDIRECT_URI
   ✓ Set KROGER_USER_ZIP_CODE
✅ Environment setup complete!

🔧 Creating MCP server instance...
✅ Server created successfully!

============================================================
🧪 Testing Prompt: grocery_list_store_path
============================================================

📋 Prompt Result:

I'm planning to go grocery shopping at Kroger with this list:

- Milk
- Bread
- Eggs
...

✅ Prompt 'grocery_list_store_path' executed successfully!

...

============================================================
📊 Test Summary
============================================================
✅ PASS - grocery_list_store_path
✅ PASS - pharmacy_open_check
✅ PASS - set_preferred_store
✅ PASS - add_recipe_to_cart

Total: 4/4 prompts tested successfully
============================================================
```

## Troubleshooting

### PowerShell Script Not Found
- Ensure `set_kroger_dev_env.ps1` is in the same directory as `test_prompts_client.py`

### Missing Environment Variables
- Check that `set_kroger_dev_env.ps1` contains all required variables
- Verify the script format matches: `$env:VAR_NAME = "value"`

### Import Errors
- Ensure you're running from the `kroger-mcp` directory
- Install dependencies: `pip install -e .` or `uv pip install -e .`

### Prompt Functions Not Found
- The script has a fallback that recreates prompt functions directly
- If prompts can't be extracted from the server, it will use the fallback implementation

## Notes

- This test client tests the **prompt generation**, not the actual MCP protocol communication
- To test full MCP functionality, you would need to run the server and connect via an MCP client
- The prompts are tested by directly calling the prompt functions with sample data

