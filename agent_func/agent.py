from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain.chat_models import init_chat_model
from typing import Annotated
from typing_extensions import TypedDict, Literal, List
from langgraph.graph import StateGraph, START, END
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from pathlib import Path
from dotenv import load_dotenv
import getpass
import json
import re
#Не забудь изменить путь на абсолютный
import prompts

load_dotenv()

DB_SETTINGS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

db = SQLDatabase.from_uri(f"postgresql://{DB_SETTINGS['user']}:{DB_SETTINGS['password']}@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['dbname']}")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_SCHEMA_JSON = DATA_DIR / "db_schema.json"

with DB_SCHEMA_JSON.open("r", encoding="utf-8") as f:
        db_schema = json.load(f)
        db_schema_str = json.dumps(db_schema, ensure_ascii=False, indent=2)

class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]

class Route(BaseModel):
    step: Literal["market_insight", "legal_help", "no_info"] = Field(
        None, description="The next step in the routing process"
    )

llm = init_chat_model("gpt-4o-mini", model_provider="openai")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = Chroma(
    collection_name="law_resources",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",
)

# State
class State(TypedDict):
    question: str
    decision: str
    optimized_question: str
    context: List[Document]
    query: str
    sql_query_result: str
    answer: str

def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = prompts.create_sql_query.invoke({"input": state["question"], "dialect": db.dialect, "top_k": 10, "table_info": db_schema_str})
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}

def execute_query(state: State):
    """Execute SQL query. DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database."""
    SELECT_ONLY = re.compile(r"^\s*(select|with)\b", re.IGNORECASE | re.DOTALL)
    if not SELECT_ONLY.match(state["query"]):
        return None
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"sql_query_result": execute_query_tool.invoke(state["query"])}

def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = prompts.answer_market.invoke({"question": state["question"], "query": state["query"], "sql_query_result": state["sql_query_result"]})
    response = llm.invoke(prompt)
    return {"answer": response.content}

def optimize(state: State):
    prompt = prompts.optimize_question.invoke({"question": state["question"]})
    response = llm.invoke(prompt)
    return {"optimized_question": response.content}

# Define application steps
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["optimized_question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    prompt = prompts.answer_legal.invoke({"question": state["optimized_question"], "context": docs_content})
    response = llm.invoke(prompt)
    return {"answer": response.content}

def no_info_print(state: State):
    print("Cannot answer your question based on information I have")

def llm_call_router(state: State):
    """Route the input to the appropriate node"""
    router = llm.with_structured_output(Route)
    prompt = prompts.route_logic.invoke({"question": state["question"]})
    decision = router.invoke(prompt)

    return {"decision": decision.step}

# Conditional edge function to route to the appropriate node
def route_decision(state: State):
    # Return the node name you want to visit next
    if state["decision"] == "market_insight":
        return "write_query"
    elif state["decision"] == "legal_help":
        return "optimize"
    elif state["decision"] == "no_info":
        return "no_info_print"


graph = StateGraph(State)

graph.add_node("write_query", write_query)
graph.add_node("execute_query", execute_query)
graph.add_node("generate_answer", generate_answer)
graph.add_node("optimize", optimize)
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_node("llm_call_router", llm_call_router)
graph.add_node("no_info_print", no_info_print)

graph.add_edge(START, "llm_call_router")
graph.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {  # Name returned by route_decision : Name of next node to visit
        "write_query": "write_query",
        "optimize": "optimize",
        "no_info_print": "no_info_print",
    },
)
graph.add_edge("write_query", "execute_query")
graph.add_edge("execute_query", "generate_answer")
graph.add_edge("generate_answer", END)


graph.add_edge("optimize", "retrieve")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)

graph.add_edge("no_info_print", END)


router_workflow = graph.compile()
state = router_workflow.invoke({"question": "Kdo má opravit poruchu v bytě, když oprava stojí víc než 2000 korun – pronajímatel nebo nájemce?"})
print(state)