"""
This is a Flask server that provides an endpoint to query a csv file with
natural language questions.
"""

import os
from src.parse_args import args
from src.data_processor.schema_graph import SchemaGraph
from src.demos.demos import Text2SQLWrapper
from src.trans_checker.args import args as cs_args
import src.utils.utils as utils

from flask import Flask, request
from io import StringIO
from pathlib import Path
import sqlite3
import pandas as pd
import configparser

# Set model ID
args.model_id = utils.model_index[args.model]
assert(args.model_id is not None)

ROOT_SECTION = 'root'
CONFIG_FILE_PATH = 'Bot/src/main/resources/bot.properties'

def loadConfig():
    ini_str = '[' + ROOT_SECTION + ']\n' + open(CONFIG_FILE_PATH, 'r').read()
    ini_fp = StringIO(ini_str)
    config = configparser.RawConfigParser()
    config.read_file(ini_fp)
    return config

def setup(args):
    csv_name = config.get(ROOT_SECTION, 'xls.importer.xls')[:-4]
    csv_dir = config.get(ROOT_SECTION, 'CSV_DIR')
    
    global db_path
    db_path = os.path.join(csv_dir, '{}.sqlite'.format(csv_name))
    
    print("* db_path = " + db_path + "\n")
    schema = SchemaGraph(csv_name, db_path=db_path)
    csv_path = os.path.join(csv_dir, '{}.csv'.format(csv_name))
    if not os.path.exists(db_path):    
        Path(db_path).touch()
        conn = sqlite3.connect(db_path)
        csv = pd.read_csv(csv_path)
        csv.to_sql(csv_name, conn, if_exists='append', index = False)
        conn.close()
    #in_type = os.path.join(csv_dir, '{}.types'.format(csv_name))
    schema.load_data_from_csv_file(csv_path)#, in_type)
    
    schema.pretty_print()

    return Text2SQLWrapper(args, cs_args, schema), schema

config = loadConfig()
app = Flask(__name__)
app.config['SERVER_NAME'] = config.get(ROOT_SECTION, 'SERVER_URL')
t2sql, schema = setup(args)

@app.route('/' + config.get(ROOT_SECTION, 'RUN_MODEL_ENDPOINT_TABLE'), methods=['POST'])
def runModelSQL():
    body = request.get_json()
    input_text = body["input"]
    
    output = t2sql.process(input_text, schema.name)
    sql_query = output['sql_query']
    
    conn = sqlite3.connect(db_path)
    c =conn.cursor()
    c.execute(sql_query)
    header = []
    for column in c.description:
        header.append(column[0])
    table = c.fetchall()
    print("* input = " + input_text)
    print("* sql = " + sql_query)
    print("* header = " + str(header))
    print("* table = " + str(table))
    print()
    response = {
        "input": input_text,
        "sql": sql_query,
        "header": header,
        "table": table
    }
    return response, 200

if __name__ == '__main__':
    app.run(debug=False)
