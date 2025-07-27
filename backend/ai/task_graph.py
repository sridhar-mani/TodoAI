import os
from dotenv import load_dotenv
import google.generativeai as genai
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from typing import List, Optional, TypedDict, Annotated
from ai.task_tools import create_task, update_task, delete_task, list_task, filter_tasks

load_dotenv()

tools = [create_task, update_task, delete_task, list_task, filter_tasks]
tools_executor = ToolNode(tools=tools, name="task_tools")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0,
    top_p=0.95,
    top_k=40,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

model_with_tools = llm.bind_tools(tools=tools)

system_prompt = SystemMessage(
    content="You are a task management agent. Parse user chat for intents like create/update/delete/list/filter tasks. Use tools appropriately. Respond concisely."
)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def agent(state):
    messages = [system_prompt]+state['messagess']
    response = model_with_tools.invoke(messages)
    return {
        "messages": messages+[response]
    }

def route_tools(state: AgentState):
    return tools_condition(state=state)

graph = StateGraph(
    state_schema=AgentState
)

graph.add_node('agent',agent)
graph.add_node('tools',tools_executor)
graph.set_entry_point('agent')
graph.add_conditional_edges('agent',route_tools,{'tools':'tools', END: END})
graph.add_edge('tools','agent')

checkpointer = MemorySaver()
compiled_graph = graph.compile(
    checkpointer=checkpointer
)