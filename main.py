import datetime
import firebase_admin
import inverterNew
import itertools
import logging
import relevancy_v2
import time

from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, render_template, request, jsonify
from google.cloud import datastore
from inverterNew_v3 import index_api_request
from query_interpreter import query_proc, entity_filter, space_filter


# Initialising Logs
format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
logging.info(" > Main    : Loading App ... ")

# Initialising the FireBase Client for continuously getting the state variables
logging.info(" > Main    : Initializing Firebase connection...")
firebase_credential = credentials.Certificate('ir-wot-ugr-credential.json')
firebase_app = firebase_admin.initialize_app(firebase_credential)

# Getting access to Firebase instance
firebase_db = firestore.client()
logging.info(" > Main    : Firebase connection initialised")

# Instantiating Flask App
app = Flask(__name__, static_url_path='/static')


# --------------------------------------------------------------------------------------------------------------------


@app.route('/')
def root():
    return render_template('search.html')


@app.route('/results', methods=['GET', 'POST'])
def query_ui():
    results = {}
    page_results = 10
    num_results = 0

    # Gathering "co_query" as the content-based query entered by the end user.
    time_begin_irwot = time.perf_counter_ns()
    query = query_proc()
    co_query = query["co_query"]
    # location_input = query["location_input"]
    if co_query == "":
        co_query = "None"
    else:
        None

    # Gathering "N" as the total number of XML Documents in the collection
    collection_n_ref = firebase_db.collection("indexStats").document("DocN")
    n_doc = collection_n_ref.get()
    n_stats = n_doc.to_dict()
    N = n_stats["N"]

    # Gathering "index_stats" as the total number of words within each of the XML Documents in the collection
    collection_stats_ref = firebase_db.collection("indexStats").document("Stats")
    stats_doc = collection_stats_ref.get()
    index_stats = stats_doc.to_dict()

    # instantiating the index pointer reference to Firebase
    index_ref = firebase_db
    results = relevancy_v2.relevance(co_query, index_ref, index_stats, N, "BM25", False)
    # ***
    # print("Printing Results ...")
    # print(results)

    if results:
        # Applying Content-and-Structure (CAS) filters

        # - Entity Restrictions
        # print(query["document_input"])
        entity_restricted_results = entity_filter(results, query["document_input"])
        results = entity_restricted_results

        # - Location Restrictions
        # print(query["spatial_input"])
        space_restricted_results = space_filter(results, query["spatial_input"], query["location_input"])
        results = space_restricted_results

        # - Time Restrictions
        # time_restricted_results = time_filter(results, query["temporal_input"])

        # - Context Restrictions
        # print("The context restrictions are: ... ")
        # print(query["cas_property"])
        # print(query["cas_action"])
        # print(query["cas_event"])
        if query["cas_property"] == "" and query["cas_action"] == "" and query["cas_event"] == "":
            None
        elif query["cas_property"] is not "":
            cas_query = query["cas_property"]
            cas_property_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            # print("Printing Property Results ... ")
            # print(cas_property_results)
            intersection = {x:results[x] for x in results if x in cas_property_results}
            # print(intersection)
            results = intersection
        elif query["cas_action"] is not "":
            cas_query = query["cas_action"]
            cas_action_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection = {x:results[x] for x in results if x in cas_action_results}
            # print(intersection)
            results = intersection
        elif query["cas_event"] is not "":
            cas_query = query["cas_event"]
            cas_event_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection = {x: results[x] for x in results if x in cas_event_results}
            # print(intersection)
            results = intersection
        elif query["cas_property"] is not "" and query["cas_action"] is not "":
            cas_query = query["cas_property"]
            cas_property_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection_property = {x: results[x] for x in results if x in cas_property_results}
            cas_query = query["cas_action"]
            cas_action_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection = {x: intersection_property[x] for x in intersection_property if x in cas_action_results}
            results = intersection
        elif query["cas_property"] is not "" and query["cas_event"] is not "":
            cas_query = query["cas_property"]
            cas_property_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection_property = {x: results[x] for x in results if x in cas_property_results}
            cas_query = query["cas_event"]
            cas_event_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection = {x: intersection_property[x] for x in intersection_property if x in cas_event_results}
            results = intersection
        elif query["cas_action"] is not "" and query["cas_event"] is not "":
            cas_query = query["cas_action"]
            cas_action_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection_action = {x: results[x] for x in results if x in cas_action_results}
            cas_query = query["cas_event"]
            cas_event_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection = {x: intersection_action[x] for x in intersection_action if x in cas_event_results}
            results = intersection
        elif query["cas_property"] is not "" and query["cas_action"] is not "" and query["cas_event"] is not "":
            cas_query = query["cas_property"]
            cas_property_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection_property = {x: results[x] for x in results if x in cas_property_results}
            cas_query = query["cas_action"]
            cas_action_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection_action = {x: intersection_property[x] for x in intersection_property if x in cas_action_results}
            cas_query = query["cas_event"]
            cas_event_results = relevancy_v2.relevance(cas_query, index_ref, index_stats, N, "BM25", True)
            intersection = {x: intersection_action[x] for x in intersection_action if x in cas_event_results}
            results = intersection
    else:
        None
        # Your search did not match any documents.

    # Limit the Number of Results and Count Total of Results
    # Get first N items in dictionary
    # print("Number of Results")
    num_results = len(results.keys())
    results = dict(itertools.islice(results.items(), page_results))
    limit_results = len(results.keys())

    time_end_irwot = time.perf_counter_ns()
    time_delta_irwot = time_end_irwot - time_begin_irwot
    print("Tiempo de Respuesta en (secs): ...")
    print(time_delta_irwot/1000000000)
    time_query = time_delta_irwot/1000000000

    return render_template('results.html', query=query, results={'Docs-Score': results}, num_results=num_results,
                           limit_results=limit_results, time_query=time_query)


@app.route('/architecture')
def about():
    return render_template('architecture.html')


@app.route('/instructions')
def instructions():
    return render_template('instructions.html')


@app.route('/settings', methods=['GET', 'POST'])
def settings():

    # local or cloud
    settings_method = "local"

    if settings_method == "local":
        ir_settings = {}
        ir_settings['index-structure'] = "hash-redblack"
        ir_settings['user-interface'] = "ui-A"
        ir_settings['model-ranking'] = "bm25"
        ir_settings['index-strategy'] = "element-incremental"
    else:
        # Instantiates a Datastore client
        datastore_client = datastore.Client()
        key = datastore_client.key('Settings', 'ir-wot-settings')
        ir_settings = datastore_client.get(key)

    if request.method == 'POST':
        new_index_structure = request.form["index-structure"]
        new_user_interface = request.form["user-interface"]
        new_model_ranking = request.form["model-ranking"]
        new_index_strategy = request.form["index-strategy"]

        if settings_method == "local":
            ir_settings['index-structure'] = new_index_structure
            ir_settings['user-interface'] = new_user_interface
            ir_settings['model-ranking'] = new_model_ranking
            ir_settings['index-strategy'] = new_index_strategy
        else:
            with datastore_client.transaction():
                key = datastore_client.key('Settings', 'ir-wot-settings')
                ir_settings = datastore_client.get(key)
                ir_settings['index-structure'] = new_index_structure
                ir_settings['user-interface'] = new_user_interface
                ir_settings['model-ranking'] = new_model_ranking
                ir_settings['index-strategy'] = new_index_strategy
                datastore_client.put(ir_settings)

        return render_template('settings.html', settings=ir_settings)

    return render_template('settings.html', settings=ir_settings)


@app.route('/research')
def research():
    return render_template('research.html')


# -------------------- API: IR.WoT Indexer --------------------


@app.route('/api/index', methods=['GET', 'POST'])
def api_index():
    if request.method == 'POST':
        crawling_input = request.get_json()
        collection_pipeline = crawling_input['collection-pipeline']
        index_response = index_api_request(collection_pipeline, firebase_db)
    return index_response


# -------------------- API: IR.WoT Query Interpreter --------------------


@app.route('/api/query', methods=['GET', 'POST'])
def api_interpreter():
    # if request.method == 'POST':
    #    query_input = request.get_json()
    #    query_co = query_input['co-query']
    #    query_cas = query_input['cas-query']
    #    # Where the Index will exist: --> Firebase OR MemCache **
    #    hashDoubleLinked, stats_collection = inverterNew.get_hashDoubleLinked(5)
    #    relv = relevancy.relevance(query_co, hashDoubleLinked, stats_collection, "BM25")
    #    return render_template('results.html',
    #                           query={"co_query": query_co, "nexi_query": f'//*[about(.,{query_co})]', 'Docs-Score': relv})
    #    return jsonify({"success": True, "co_query": query_co, "nexi_query": f'//*[about(.,"{query_co}")]', 'Docs-Score': relv})
    #else:
    #    return jsonify({"success": False, "Query": None})
    return


# -------------------- API: IR.WoT Experiments --------------------


@app.route('/api/experiment1', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        number_document = request.get_json()
        n = number_document["n"]
        print("Number of XML Documents: " + str(n))
        # doc_ref = firebase_db.collection('statsIRWoT').document(f'test_stats{n}')
        dt_index_inverter, t_sizes_text, t_sizes_index = inverterNew.experiment1(n)
        t1 = []
        t2 = []
        sizes_text = []
        sizes_index = []
        for i in range(len(t_sizes_text)):
            t1.append(t_sizes_text[i][0])
            t2.append(t_sizes_index[i][0])
            sizes_text.append(t_sizes_text[i][1])
            sizes_index.append(t_sizes_index[i][1])
        send = {'dt_index_inverter': {'dt': dt_index_inverter}, 't_sizes_text': {'t': t1, 'sizes_text': sizes_text}, 't_sizes_index': {'t': t2, 'sizes_index': sizes_index}}
        # print(send)
        # doc_ref.set(send)
        print('Successful response')
        return f'Successful response = {send}'
    else:
        print('No such document!')
        return 'No such document!'


# -------------------- API: IR.WoT Crawler --------------------


@app.route('/api/crawler', methods=['GET', 'POST'])
def api_crawler():
    if request.method == 'POST':
        crawling_pipe = request.get_json()
        crawling_entity_id = crawling_pipe['id-updated-entity']
        crawling_pipe_id = crawling_pipe['id-crawler-pipe']
        now = datetime.datetime.now()  # time object
        crawling_time = now

        # Instantiates a Google Datastore client
        datastore_client = datastore.Client()
        with datastore_client.transaction():
            key_pipe = datastore_client.key("Crawling_Pipe", crawling_pipe_id)
            task_insert = datastore.Entity(key=key_pipe)
            task_insert.update(
                {
                    'id-sim-entity': crawling_entity_id,
                    'created': crawling_time,
                    'state': 'inserted'
                }
            )
            datastore_client.put(task_insert)
            return jsonify({"success": True, "crawling_method": "pipe", "state": "updated"})
    elif request.method == 'GET':
        id_to_retrieve = request.args.get('id')
        # id_num_retrieve = request.args.get('number')
        # Instantiates a Google Datastore client
        datastore_client = datastore.Client()
        key_pipe = datastore_client.key("Crawling_Pipe", int(id_to_retrieve))
        # query = datastore_client.query(kind="Crawling_Pipe")
        # query.add_filter("id-sim-entity", "=", id_to_retrieve)
        # query.order = ["-created"]
        # query.keys_only()
        # query = datastore_client.query() !!!XXX
        # results = list(query.fetch())  # limit=int(id_num_retrieve)
        task_retrieve = datastore_client.get(key_pipe)
        return jsonify({"success": True, "crawling_method": "pipe", "retrieve": task_retrieve})
    else:
        return jsonify({"success": False, "Error": "simulation id not provided."})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8084, debug=True)
