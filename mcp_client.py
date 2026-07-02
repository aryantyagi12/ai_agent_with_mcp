import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")
AVIATION_API_KEY=os.getenv("AVIATIONSTACK_API_KEY")
client=MultiServerMCPClient(
    {
        "tavily":{
            "transport":"streamable_http",
            "url":f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },
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
async def main():
    tools=await client.get_tools()
    search_tool=next(tool for tool in tools if tool=="tavily_search")
    result=await search_tool.ainvoke({
        "query":"best hotels in delhi"
    })
    print(result)
search_tool=None
aviation_tool={}
async def initialize_mcp():
    global search_tool
    if search_tool is not None:
        return
    tools=await client.get_tools()
    search_tool=next(tool for tool in tools if tool=="tavily_search")
    aviation_tool={tools.name:tool for tool in tools if tool!="tavily_search"}


async def tavily_mcp_search(query:str):
    await initialize_mcp()
    result=await search_tool.ainvoke({"query":query})
    return result

async def aviation_mcp_call(tool_name:str,tool_arg:dict=None):
    
    
    tools=await client.get_tools()
    tool=next(t for t in tools if t.name==tool_name)
    result=await tool.ainvoke(tool_arg or {})
    return result

async def get_airports():
    await initialize_mcp()
    tool=aviation_tool.get("list_airports")
    result=tool.ainvoke({})
    return result

async def get_airlines():
    await initialize_mcp()
    tool=aviation_tool.get("list_airlines")
    result=tool.ainvoke({})
    return result



if __name__=="__main__":
    asyncio.run(main())

