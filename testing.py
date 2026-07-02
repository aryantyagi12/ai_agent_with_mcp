import os 
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
import asyncio


load_dotenv()

OPENWEATHER_API_KEY=os.getenv("OPENWEATHER_API_KEY")

client=MultiServerMCPClient(
    {
        "weather":{
            "transport":"stdio",
            "command":r"C:\Users\Aryan\Documents\multi_agent\.venv\Scripts\python.exe",
            "args":[r"C:\Users\Aryan\Documents\mcp_multiple_agent\custom_weather_mcp_server.py"],
            "env":{
                "OPENWEATHER_API_KEY":OPENWEATHER_API_KEY
            }

        }
    }
)

async def main():
    tools=await client.get_tools()
    for tool in tools:
        print(tool.name)

if __name__=="__main__":
    asyncio.run(main())
