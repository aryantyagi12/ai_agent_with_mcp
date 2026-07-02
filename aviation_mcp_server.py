import os 
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
load_dotenv()
AVIATION_API_KEY=os.getenv("AVIATIONSTACK_API_KEY")

client=MultiServerMCPClient(
    {
        "aviationstack":{
            "transport":"stdio",
            "command":r"C:\Users\Aryan\Documents\mcp_multiple_agent\aviationstack-mcp\.venv\Scripts\python.exe",
            "args":["-m","aviationstack_mcp","mcp","run"],
            "env":{
                "AVIATION_API_KEY":AVIATION_API_KEY
            }
        }
    }
)
import asyncio
async def main():
    tools=await client.get_tools()
    print("available tools")
    for tool in tools:
        print(tool.name)

asyncio.run(main())
