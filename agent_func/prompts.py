from langchain.prompts import PromptTemplate

create_sql_query = PromptTemplate.from_template("""
The question from a user: {input}

You are a helpful assistant. Given an input question, create a syntactically correct {dialect} query to
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
""")

optimize_question = PromptTemplate.from_template("""
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
""")

answer_legal = PromptTemplate.from_template("""
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
""")

answer_market = PromptTemplate.from_template("""
Given the following user question, corresponding SQL query, 
and SQL result, answer the user question."
                                             
    Question: {question}
    SQL Query: {query}
    SQL Result: {sql_query_result}
                                             
Answer in the language of the question.                                                                  
""")

no_info_answer = PromptTemplate.from_template("""
You help users answer questions about property and renting in the Czech Republic.
To do so, you have access to a rental listings database and a vector database containing legal information about renting in the Czech Republic.

The user has asked the following question:
{question}

After analyzing the question, it has been determined that we cannot answer the question due to this reason: {reason}.

Please respond politely. 
Keep the reply brief (1–2 sentences maximum) and include an apology explaining that you are unable to help due to mentioned reason.
Identify the language of this question "{question}" and answer in the SAME language as the question. The fact that we are talking about
Czech Republic is not the reason to answer in Czech.
""")

route_logic = PromptTemplate.from_template("""
SYSTEM PROMPT — Routing Agent

You are a helpful assistant.
Users ask you questions about property and renting in the Czech Republic.
To answer, you use a rental listings database and a vector database with legal information related to renting in the Czech Republic.                                           
                                           
Route the question to market_insight, legal_help, or no_info based on the user's question
{question}

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
""")