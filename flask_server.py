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
import sqlite3
import pandas as pd
import configparser
import re

# Set model ID
args.model_id = utils.model_index[args.model]
assert(args.model_id is not None)

ROOT_SECTION = 'root'
CONFIG_FILE_PATH = '../Bot/src/main/resources/bot.properties'

def loadConfig():
    ini_str = '[' + ROOT_SECTION + ']\n' + open(CONFIG_FILE_PATH, 'r').read()
    ini_fp = StringIO(ini_str)
    config = configparser.RawConfigParser()
    config.read_file(ini_fp)
    return config

def setup(args):
    global db_path
    csv_name = config.get(ROOT_SECTION, 'xls.importer.xls')[:-4] # Remove the extension '.csv' from the file name
    csv_dir = args.csv_dir
    db_path = os.path.join(csv_dir, '{}.sqlite'.format(csv_name))
    print('* db_path = ' + db_path + '\n')
    if os.path.exists(db_path):
        os.remove(db_path)
    schema = SchemaGraph(csv_name, db_path=db_path)
    csv_path = os.path.join(csv_dir, '{}.csv'.format(csv_name))
    delimiter = config.get(ROOT_SECTION, 'csv.delimiter').encode().decode('unicode_escape')
    conn = sqlite3.connect(db_path)
    csv = pd.read_csv(csv_path, sep=delimiter)
    print('* rows: ' + str(csv.shape[0]) + ', columns: ' + str(csv.shape[1]) + '\n')
    csv.to_sql(csv_name, conn, if_exists='append', index = False)
    conn.close()
    #in_type = os.path.join(csv_dir, '{}.types'.format(csv_name))
    schema.load_data_from_csv_file(csv_path, delimiter)#, in_type)
    schema.pretty_print()
    return Text2SQLWrapper(args, cs_args, schema), schema

config = loadConfig()
app = Flask(__name__)
app.config['SERVER_NAME'] = config.get(ROOT_SECTION, 'SERVER_URL')
t2sql, schema = setup(args)

def addFieldsToSql(fields, sql_query):
    select_all_from = re.search(r'SELECT \* FROM', sql_query)
    if select_all_from:
        select_fields_str = 'SELECT ' + fields[0]
        for f in fields[1:]:
            select_fields_str += ', {}'.format(f)
        select_fields_str += ' FROM'
        return select_fields_str + sql_query[select_all_from.span(0)[1]:]
    else:
        return sql_query

def addFiltersToSql(filters, sql_query):
    select_from_where_orderby = re.search(r'SELECT (.)* FROM (.)* WHERE (.)* ORDER BY (.)*', sql_query)
    select_from_orderby = re.search(r'SELECT (.)* FROM (.)* ORDER BY (.)*', sql_query)
    select_from_where = re.search(r'SELECT (.)* FROM (.)* WHERE (.)*', sql_query)
    select_from = re.search(r'SELECT (.)* FROM (.)*', sql_query)
    orderby_str = ''

    orderby = re.search(r'ORDER BY (.)*', sql_query)
    if select_from_where_orderby:
        orderby_str = sql_query[orderby.span(0)[0] : orderby.span(0)[1]]
        sql_query = sql_query[:orderby.span(0)[0]]
    elif select_from_orderby:
        orderby_str = sql_query[orderby.span(0)[0] : orderby.span(0)[1]]
        sql_query = sql_query[:orderby.span(0)[0]] + ' WHERE 1=1'
    elif select_from_where:
        True
    elif select_from:
        sql_query += ' WHERE 1=1'
    for f in filters:
        sql_query += ' AND ({})'.format(f)
    if orderby:
        sql_query += ' ' + orderby_str
    return sql_query
        

@app.route('/' + config.get(ROOT_SECTION, 'RUN_MODEL_ENDPOINT_TABLE'), methods=['POST'])
def runModelSQL():
    body = request.get_json()
    input_text = body['input']
    fields = body['fields']
    filters = body['filters']
    ignoreCase = body['ignoreCase']
    
    output = t2sql.process(input_text, schema.name)
    sql_query = output['sql_query']

    if sql_query is None:
        sql_query = ''
        header = []
        table = []
    else:
        if fields:
            sql_query = addFieldsToSql(fields, sql_query)
        if filters:
            sql_query = addFiltersToSql(filters, sql_query)
        if ignoreCase and re.search(r'SELECT (.)* FROM (.)* WHERE (.)*', sql_query):
            sql_query += ' COLLATE NOCASE'
        conn = sqlite3.connect(db_path)
        c =conn.cursor()
        c.execute(sql_query)
        header = []
        for column in c.description:
            header.append(column[0])
        table = c.fetchall()
    print('* input  = ' + input_text)
    print('* sql    = ' + sql_query)
    print('* header = ' + str(header))
    print('* table  = ' + str(table))
    print()
    response = {
        'input': input_text,
        'sql': sql_query,
        'header': header,
        'table': table
    }
    return response, 200

if __name__ == '__main__':
    app.run(debug=False)
