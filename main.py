import asyncio
from typing import TypedDict,Annotated
import os 
from dotenv import load_dotenv
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (AnyMessage,HumanMessage,AIMessage,SystemMessage)
import psycopg
from langchain_groq import ChatGroq



from mcp_client import tavily_mcp_search,get_airports,get_airlines,aviation_mcp_call,extract_destination,forecast_mcp_search,weather_mcp_search

load_dotenv()
llm=ChatGroq(model="llama-3.3-70b-versatile")
DATABASE_URL=os.getenv("DATABASE_URL")

class TravelState(TypedDict):
    message:Annotated[list[AnyMessage],operator.add]
    user_query:str
    flight_results:str
    hotel_results:str
    itinerary:str
    llm_calls:int
    weather_results:str


FLIGHT_AGENT_PROMPT="""
you are a travel flight expert
user query:
{query}
airport information:
{airport_data}
airline information:
{airline_data}
Generate:

1. likely departure airport
2. likely arrival airport
3. airlines serving this rout
4. typical flight duration
5. estimated airface range
6. peak season pricing warning
7. booking advice 

Return concise travel guidance.

"""

def flight_agent(state:TravelState):
    query=state["user_query"]
    try:
        airports=asyncio.run(aviation_mcp_call("list_airports"))
        airlines=asyncio.run(aviation_mcp_call("list_airlines"))
        prompt=FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:1000],
            airline_data=str(airlines)[:1000]
        )
        response=llm.invoke([
            SystemMessage(content="you are an expert travel flight planner."),
            HumanMessage(content=prompt)

        ])
        flight_data=response.content
    except Exception as e:
        flight_data=f"flight information unavailable :{str(e)}"
    return {
        "flight_data":flight_data,
        "message":[AIMessage(content="flight information fetched")],
        "llm_calls":state.get("llm_calls",0)+1
    }

def hotel_agent(state:TravelState):
    query=f"hotel search for{state['user_query']}"
    hotel_data=asyncio.run(tavily_mcp_search(query))
    return {
        "hotel_results":hotel_data,
        "message":[AIMessage(content=f"hotel information fetched")],
        "llm_calls":state.get("llm_calls",0)+1
    }

def weather_agent(state:TravelState):
    city=extract_destination(state["user_query"])
    weather_data=asyncio.run(weather_mcp_search(city))
    forecast_data=asyncio.run(forecast_mcp_search(city))
    return {
        "weather_results":f"""
        current weather in {city}:{weather_data}
        forecast for {city}:{forecast_data}
        """,
        "message":[AIMessage(content=f"weather information fetched")]
    }




def itinerary_agent(state:TravelState):
    prompt=f"""
    create a travel itinerary.
    user query:
    {state["user_query"]}
    flight results:
    {state["flight_results"]}
    hotel results:
    {state["hotel_results"]}
    weather results:
    {state["weather_results"]}
    """
    response=llm.invoke(
        [SystemMessage(content="you are an expert travel planner"),
        HumanMessage(content=prompt)]
    )
    return {
        "itinerary":response.content,
        "message":[response],
        "llm_calls":state.get("llm_calls",0)+1
    }

graph=StateGraph(TravelState)
graph.add_node("flight_agent",flight_agent)
graph.add_node("hotel_agent",hotel_agent)
graph.add_node("weather_agent",weather_agent)
graph.add_node("itinerary_agent",itinerary_agent)

graph.add_edge(START,"flight_agent")
graph.add_edge("flight_agent","hotel_agent")
graph.add_edge("hotel_agent","weather_agent")
graph.add_edge("weather_agent","itinerary_agent")
graph.add_edge("itinerary_agent",END)

_conn=psycopg.connect(DATABASE_URL)
_conn.autocommit = True
checkpointer=PostgresSaver(_conn)
checkpointer.setup()

app=graph.compile(checkpointer=checkpointer)
import uuid
if __name__=="__main__":
    config={"configurable":{"thread_id":str(uuid.uuid4())}}
    user_input=input("enter travel request")
    result=app.invoke(
        {
            "message":[HumanMessage(content=user_input)],
            "user_query":user_input,
            "flight_results":"",
            "hotel_results":"",
            "itinerary":"",
            "llm_calls":0
        },
        config=config
    )
    print("\nfinal output\n")
    print(result["message"][-1].content)


