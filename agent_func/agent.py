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
from dotenv import load_dotenv
import getpass
import json
import re

load_dotenv()

DB_SETTINGS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

db = SQLDatabase.from_uri(f"postgresql://{DB_SETTINGS['user']}:{DB_SETTINGS['password']}@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['dbname']}")

with open("../data/db_schema.json", "r", encoding="utf-8") as f:
        db_schema = json.load(f)
        db_schema_str = json.dumps(db_schema, ensure_ascii=False, indent=2)

system_message_market_insight = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Unless the user specifies in his question a
specific number of examples they wish to obtain, always limit your query to
at most {top_k} results. You can order the results by a relevant column to
return the most interesting examples in the database.

Never query for all the columns from a specific table, only ask for a the
few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

There is only one table in the Database named "properties". Use the following info about the table:
{table_info}
"""
user_prompt_market_insight = "Question: {input}"

query_prompt_template = ChatPromptTemplate(
    [("system", system_message_market_insight), ("user", user_prompt_market_insight)]
)

class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]

system_message_legal_help = PromptTemplate(
    input_variables=["question"],
    template="""
You are a helpful assistant. Your task is to optimize the user's question for better vector‑store similarity search.

One document in the vector store looks like:
Document(id='e6a24daa-1c26-49a9-bb78-6ef31a76eedb',
 metadata={{'section_number': 2246,
            'section_title': 'Nájemné a jiné platby',
            'seq_num': 12,
            'source': '/Users/aznaur/Desktop/pet_project/property_price_project/rag/czech_civil_code.json',
            'source_name': 'Občanský zákoník č. 89/2012 Sb.',
            'url': 'https://www.zakonyprolidi.cz/cs/2012-89#p2246'}},
 page_content='§ 2246 …')

Question:
{question}

Optimized Question:
"""
)

system_message_legal_help_2 = PromptTemplate(
    input_variables=["context", "question"],
    template="""
Use the following context to answer the question.
If the answer is not found in the context, say "I'm sorry, I don't have the necessary resources to answer your question.".

Context:
{context}

Question:
{question}

When answering the question, include the document title taken from its 
source_name metadata field (e.g. Občanský zákoník č. 89/2012 Sb.) and, if relevant, the paragraph/section number taken from its section_number metadata field.
Answer in the language of the question, but documents name in the original language.

Answer:
"""
)

if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

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
    query: str
    decision: str
    result: str
    answer: str
    optimized_question: str
    context: List[Document]

def write_query(state: State):
    """Generate SQL query to fetch information."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db_schema_str,
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}

def execute_query(state: State):
    """Execute SQL query.
    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database."""
    SELECT_ONLY = re.compile(r"^\s*(select|with)\b", re.IGNORECASE | re.DOTALL)
    if not SELECT_ONLY.match(state["query"]):
        return None
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}

def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}

def optimize(state: State):
    message = system_message_legal_help.invoke({"question": state["question"]})
    response = llm.invoke(message)
    return {"optimized_question": response.content}

# Define application steps
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["optimized_question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = system_message_legal_help_2.invoke({"question": state["optimized_question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}

def no_info_print(state: State):
    print("Cannot answer your question based on information I have")

def llm_call_router(state: State):
    """Route the input to the appropriate node"""

    # Run the augmented LLM with structured output to serve as routing logic
    decision = router.invoke(
        [
            SystemMessage(
                content="""
                SYSTEM PROMPT — Routing Agent  
                Route the question to market_insight, legal_help, or no_info based on the user's request  
                
                The value of step must be one of:

                - "market_insight" – use this when the user is asking about market-level facts or statistics that can be answered from the rental-ads database.  
                • Typical cues: price, rent level, fees, deposits, trends, averages, comparisons between districts, flat sizes or time periods, “how much”, “where is cheaper”, “average deposit”, etc.  
                • The database you can rely on contains the table **Properties** with columns such as `Price`, `ServiceFees`, `EnergyFees`, `RefundableDeposit`, `Layout`, `City`, `District`, `UsableArea`, dates, amenities, etc.  
                • Do **not** choose this route for purely legal, contractual, or regulatory queries.

                - "legal_help" – use this when the user’s question concerns legal rights, duties or regulations related to renting property in Czechia.  
                • Typical cues: tenancy contracts, notice periods, eviction, rent increase rules, landlord / tenant obligations, deposits refund rules, maintenance responsibilities, service-charge settlement, tax duties.  
                • Answers will be produced by searching a vector knowledge-base built from:  
                    – *Občanský zákoník* (Act No. 89/2012 Sb.) §2235-2301  
                    – *Zákon č. 67/2013 Sb.* (About service charges)  
                • Do **not** choose this route if the question is just about prices or market statistics.

                - "no_info" – choose this only if:  
                • the question is completely unrelated to renting property, **or**  
                • it is about renting but cannot be answered by either the Properties table (market data) **nor** the two Czech legal sources above (legal data).
            """
            ),
            HumanMessage(content=state["question"]),
        ]
    )

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


# Schema for structured output to use as routing logic
class Route(BaseModel):
    step: Literal["market_insight", "legal_help", "no_info"] = Field(
        None, description="The next step in the routing process"
    )

# Augment the LLM with schema for structured output
router = llm.with_structured_output(Route)

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
state = router_workflow.invoke({"question": "What is the average price for 2+kk in Prague?"})
print(state)