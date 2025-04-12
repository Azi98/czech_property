import utils.create_request_llm as cr
import utils.pg_execute_query as eq

prompt = "Какая средняя цена на Garsoniéra в Праге?"

def main():
    sql_request = cr.create_sql_request("data/db_schema.json", prompt, debug=True)
    eq.execute_query(sql_request)

if __name__ == "__main__":
    main()