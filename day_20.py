import pytest
import os
from dotenv import load_dotenv
from typing import TypedDict
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "openai/gpt-oss-20b"

class AgentState(TypedDict):
    query: str
    context: str
    final_answer: str
    next_node: str

llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

def researcher_agent(state: AgentState):
    retrieved_data = "ChromaDB and Milvus use approximate nearest neighbor algorithms."
    return {"context": retrieved_data}

def writer_agent(state: AgentState):
    response = llm.invoke(f"Write a summary based on: {state['context']}")
    return {"final_answer": response.content}

def supervisor_node(state: AgentState):
    if not state.get("context"):
        return {"next_node": "researcher"}
    elif not state.get("final_answer"):
        return {"next_node": "writer"}
    return {"next_node": "END"}

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("researcher", researcher_agent)
workflow.add_node("writer", writer_agent)

workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges("supervisor", lambda state: state["next_node"], {
    : "researcher",
    : "writer",
    : END
})
workflow.add_edge("researcher", "supervisor")
workflow.add_edge("writer", "supervisor")

app = workflow.compile()

def run_agents(query: str):
    result = app.invoke({"query": query})
    return result["final_answer"]

class GroqEvaluator(DeepEvalBaseLLM):
    def __init__(self, model_name="llama3-70b-8192"):
        self.model_name = model_name
        self.model = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)

    def load_model(self):
        return self.model

    def generate(self, prompt: str, *args, **kwargs) -> str:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str, *args, **kwargs) -> str:
        res = await self.model.ainvoke(prompt)
        return res.content

    def get_model_name(self):
        return self.model_name

def test_agent_accuracy():
    user_query = "How do ChromaDB and Milvus handle search?"
    actual_output = run_agents(user_query)
    expected_context = [

    ]

    test_case = LLMTestCase(
        input=user_query,
        actual_output=actual_output,
        retrieval_context=expected_context
    )

    groq_judge = GroqEvaluator()
    faithfulness = FaithfulnessMetric(threshold=0.8, model=groq_judge)
    relevancy = AnswerRelevancyMetric(threshold=0.8, model=groq_judge)

    assert_test(test_case, [faithfulness, relevancy])
