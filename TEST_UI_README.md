# Kroger MCP Prompts Test UI

A web-based UI for testing all 4 Kroger MCP prompts interactively.

## Overview

This Streamlit-based web application provides a user-friendly interface to:
- ✅ View all available prompts
- ✅ Test prompts with custom parameters
- ✅ See prompt results in real-time
- ✅ Download results as text files

## Prerequisites

- Python 3.10+
- Streamlit: `pip install streamlit`
- MCP SDK: `pip install mcp`
- All dependencies from `pyproject.toml` installed

## Installation

```bash
# Install Streamlit (if not already installed)
pip install streamlit

# Install MCP SDK (if not already installed)
pip install mcp
```

## Usage

### Starting the UI

```bash
# From the kroger-mcp directory
streamlit run test_prompts_ui.py
```

This will:
1. Start the Streamlit web server
2. Open your browser automatically (usually at http://localhost:8501)
3. Connect to the MCP server automatically when testing prompts

### Using the UI

1. **Select a Prompt**: Choose from the dropdown menu which prompt you want to test
2. **Enter Parameters**: Fill in any required parameters for the selected prompt:
   - **grocery_list_store_path**: Enter your grocery list
   - **pharmacy_open_check**: No parameters needed
   - **set_preferred_store**: Enter a zip code
   - **add_recipe_to_cart**: Enter a recipe type
3. **Test Prompt**: Click the "🚀 Test Prompt" button
4. **View Results**: See the generated prompt text in the result area
5. **Download**: Optionally download the result as a text file

## Features

### Prompt Information
- View prompt name and description
- See required/optional arguments
- Understand what each prompt does

### Interactive Testing
- Real-time prompt generation
- Custom parameter input
- Immediate results display

### Result Management
- View formatted prompt results
- Download results as text files
- Copy results to clipboard

## UI Screenshots

### Main Interface
- Clean, modern design
- Sidebar navigation
- Status indicators
- Prompt selection dropdown

### Testing Interface
- Parameter input forms
- Large result display area
- Download button
- Success/error indicators

## Available Prompts

1. **grocery_list_store_path**
   - **Purpose**: Optimize shopping path through store
   - **Parameters**: `grocery_list` (text area)
   - **Example**: List of grocery items

2. **pharmacy_open_check**
   - **Purpose**: Check if pharmacy is open
   - **Parameters**: None
   - **Example**: No input needed

3. **set_preferred_store**
   - **Purpose**: Set preferred Kroger store
   - **Parameters**: `zip_code` (text input)
   - **Example**: "45202"

4. **add_recipe_to_cart**
   - **Purpose**: Find recipe and add ingredients to cart
   - **Parameters**: `recipe_type` (text input)
   - **Example**: "chocolate chip cookies"

## Troubleshooting

### Streamlit Not Found
```bash
pip install streamlit
```

### MCP SDK Not Available
```bash
pip install mcp
```

### Server Connection Failed
- Make sure `run_server.py` exists in the same directory
- Check that environment variables are set (if needed)
- The UI will start the server automatically via stdio

### Port Already in Use
If port 8501 is already in use:
```bash
streamlit run test_prompts_ui.py --server.port 8502
```

### Browser Doesn't Open
Manually navigate to: http://localhost:8501

## Advanced Usage

### Custom Port
```bash
streamlit run test_prompts_ui.py --server.port 8502
```

### Headless Mode (no browser)
```bash
streamlit run test_prompts_ui.py --server.headless true
```

### Custom Theme
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

## Comparison with Other Test Scripts

- **`test_prompts_client.py`**: Command-line, full setup, automated testing
- **`test_prompts_client_running_server.py`**: Command-line, focused on testing
- **`test_prompts_ui.py`**: Web UI, interactive, user-friendly

## Notes

- The UI uses stdio transport to connect to the MCP server
- The server is started automatically when testing prompts
- Results are displayed in real-time
- All prompts are tested individually (not in batch)

## Development

To modify the UI:
1. Edit `test_prompts_ui.py`
2. Streamlit will auto-reload on save
3. Refresh the browser to see changes

## Support

For issues or questions:
- Check the main README.md
- Review the MCP SDK documentation
- Check Streamlit documentation: https://docs.streamlit.io/

