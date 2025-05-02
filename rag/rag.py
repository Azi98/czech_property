"""Тут уже рабочий код с использованием RAG. Нужный вопрос задай в переменную result"""

from typing_extensions import List, TypedDict, Annotated
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langgraph.graph import START, StateGraph
import os
import getpass
from langchain_core.documents import Document
from langchain.chat_models import init_chat_model
import json
from pydantic import ValidationError, BaseModel, Field

# Load variables from the .env file
load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")


llm = init_chat_model("gpt-4o-mini", model_provider="openai")

prompt_1 = PromptTemplate(
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

prompt_2 = PromptTemplate(
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


embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = Chroma(
    collection_name="czech_civil_code_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",
)

# Define state for application
class State(TypedDict):
    question: str
    optimized_question: str
    context: List[Document]
    answer: str


def optimize(state: State):
    message = prompt_1.invoke({"question": state["question"]})
    response = llm.invoke(message)
    return {"optimized_question": response.content}

# Define application steps
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt_2.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}


graph_builder = StateGraph(State).add_sequence([optimize, retrieve, generate])
graph_builder.add_edge(START, "optimize")
graph = graph_builder.compile()

result = graph.invoke({"question": "Может ли арендодатель поднять аренду в середине контракта?"})
#result = graph.invoke({"question": "Какая самая дорогая кварира в Праге?"})

print(f'Context: {result["context"]}\n\n')
print(f'Answer: {result["answer"]}')
print(f'Optimized question: {result["optimized_question"]}')

