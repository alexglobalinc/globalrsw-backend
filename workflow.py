# workflow.py
from typing import Annotated, Dict, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, Graph, END
from langgraph.graph.message import AnyMessage, add_messages
from langchain_openai import ChatOpenAI
#from tools import DatabaseTools, get_db_connection
from copilotkit.langchain import copilotkit_emit_message, copilotkit_emit_state, copilotkit_customize_config
import config
from langgraph.checkpoint.memory import MemorySaver

from typing import Annotated, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain import hub
from tools import get_sql_toolkit
from copilotkit.langchain import copilotkit_emit_message
import operator

import asyncio

class AgentState(TypedDict):
    """State object for the agent."""
    messages: Annotated[List[BaseMessage], operator.add]
    processed_messages: set  # Add this to track processed messages

class DatabaseAnalysisGraph:
    def __init__(self):
        self.toolkit = get_sql_toolkit()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Create the LangGraph workflow using ReAct agent."""
        prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
        system_message = prompt_template.format(dialect="T-SQL", top_k=5)
        
        agent = create_react_agent(
            self.toolkit.llm,
            self.toolkit.get_tools()
        )

        memory = MemorySaver()
        workflow = StateGraph(AgentState)
        
        async def agent_node(state, config):
            # Initialize processed_messages if it doesn't exist
            if 'processed_messages' not in state:
                state['processed_messages'] = set()
                
            message_id = state["messages"][-1].content if state["messages"] else None
            
            # Check if we've already processed this message
            if message_id and message_id in state['processed_messages']:
                return state
                
            await copilotkit_emit_state(config, {
                "messages": state["messages"],
                "currentNode": "agent",
                "status": "inProgress",
                "messageId": message_id
            })

            try:
                response = await agent.ainvoke(state, config)
                
                if "messages" in response and response["messages"]:
                    message_content = response["messages"][-1].content
                    if message_id:
                        state['processed_messages'].add(message_id)
                        
                    await copilotkit_emit_message(config, message_content)
                    await copilotkit_emit_state(config, {
                        "messages": response["messages"],
                        "currentNode": "agent",
                        "status": "inProgress",
                        "messageId": message_id
                    })
                    
                return response

            finally:
                await copilotkit_emit_state(config, {
                    "messages": state["messages"],
                    "currentNode": "agent",
                    "status": "complete",
                    "messageId": message_id
                })

        workflow.add_node("agent", agent_node)
        workflow.set_entry_point("agent")
        workflow.add_edge("agent", END)

        return workflow.compile(checkpointer=memory)

    async def run(self, query: str):
        """Process a natural language query through the graph."""
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "processed_messages": set()  # Initialize the set
        }
        
        return await self.graph.ainvoke(initial_state)

# Create graph instance
graph = DatabaseAnalysisGraph().graph