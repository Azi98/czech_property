from flask import Flask
import utils.create_request_llm as cr
import utils.pg_execute_query as eq

app = Flask(__name__)

@app.route('/legal')
def index():
    return 'Hello, World!'

@app.route('/property_data')
def retrieve_data():
    prompt = "Какая средняя цена на Garsoniéra в Праге?"
    sql_request = cr.create_sql_request("data/db_schema.json", prompt, debug=True)
    result = eq.execute_query(sql_request)
    return str(result)

if __name__ == '__main__':
    app.run(debug=True)

