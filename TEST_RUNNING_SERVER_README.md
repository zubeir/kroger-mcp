# Test Prompts Client for Running Server

This script (`test_prompts_client_running_server.py`) tests all 4 Kroger MCP prompts against a running MCP server.

## Overview

The test client will:
1. ✅ Connect to the Kroger MCP server
2. ✅ List all available prompts
3. ✅ Test all 4 registered prompts:
   - `grocery_list_store_path` - Optimize shopping path
   - `pharmacy_open_check` - Check pharmacy hours
   - `set_preferred_store` - Set preferred Kroger store
   - `add_recipe_to_cart` - Find recipe and add ingredients
4. ✅ Display results and summary

## Prerequisites

- Python 3.10+
- MCP SDK: `pip install mcp`
- Kroger MCP server (will be started automatically with stdio transport)

## Usage

### Basic Usage (stdio transport - recommended)

The script will automatically start the server when using stdio transport:

```bash
# From the kroger-mcp directory
python test_prompts_client_running_server.py
```

This will:
- Start the server automatically via stdio
- Connect to it as an MCP client
- Test all prompts
- Shut down the server when done

### Testing Against a Pre-Running Server

If you want to test against a server that's already running separately:

**Terminal 1 - Start the server:**
```bash
# Start server with SSE transport
python -m kroger_mcp.cli --transport sse --port 8000
```

**Terminal 2 - Run the test client:**
```bash
# Note: SSE client connection is not yet fully implemented
# For now, use stdio transport which starts the server automatically
python test_prompts_client_running_server.py
```

## Command Line Options

```bash
python test_prompts_client_running_server.py [OPTIONS]

Options:
  --transport {stdio,sse}  Transport protocol (default: stdio)
  --host HOST              Host for SSE transport (default: 127.0.0.1)
  --port PORT              Port for SSE transport (default: 8000)
```

## Test Output

The script will output:
- ✅ Connection status
- 📋 List of available prompts
- 📋 Generated prompt text for each test
- ✅/❌ Pass/fail status for each prompt
- 📊 Summary of all test results

## Example Output

```
============================================================
🛒 Kroger MCP Prompts Test Client
   Testing against running server
============================================================

🔌 Connecting to MCP server via stdio...
📡 Establishing connection via stdio...
   (This will start the server automatically)
🔧 Initializing MCP session...

📋 Listing available prompts...
✅ Found 4 prompts:
   - grocery_list_store_path
   - pharmacy_open_check
   - set_preferred_store
   - add_recipe_to_cart

============================================================
🧪 Testing Prompt: grocery_list_store_path
============================================================

📋 Prompt Result:
I'm planning to go grocery shopping at Kroger with this list:

- Milk
- Bread
...

✅ PASS

...

============================================================
📊 Test Summary
============================================================
✅ PASS - grocery_list_store_path
✅ PASS - pharmacy_open_check
✅ PASS - set_preferred_store
✅ PASS - add_recipe_to_cart

Total: 4/4 prompts tested successfully
🎉 All prompts tested successfully!
============================================================
```

## Differences from `test_prompts_client.py`

- **`test_prompts_client.py`**: 
  - Sets up environment from PowerShell script
  - Creates `.env` file
  - Starts server and tests prompts
  - More comprehensive setup

- **`test_prompts_client_running_server.py`**:
  - Simpler, focused on testing prompts
  - Assumes environment is already set up
  - Can connect to already-running server (with SSE transport)
  - Lighter weight for quick testing

## Troubleshooting

### MCP SDK Not Found
```bash
pip install mcp
```

### Server Connection Failed
- Make sure the server script (`run_server.py`) exists
- Check that environment variables are set (if needed)
- For stdio transport, the server will start automatically

### No Prompts Found
- Verify the server is running correctly
- Check that prompts are registered in the server
- Ensure you're using the correct server instance

## Notes

- The stdio transport will start the server automatically
- For testing against a truly separate running server, SSE transport support needs to be implemented
- The script uses the MCP SDK's `stdio_client` which manages the server lifecycle

