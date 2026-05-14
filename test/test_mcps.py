import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcps.server import mcp

def test_mcp_schema():
    tools = mcp.list_tools()
    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"Schema: {json.dumps(tool.inputSchema, indent=2)}")
    
    
if __name__ == "__main__":
    test_mcp_schema()