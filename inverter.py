# import firebase_admin
import logging
import requests
import xml.etree.ElementTree as ElementTree
import sys
import time
from pyllist import dllist
import memObj
# import relevancy


# from firebase_admin import credentials
# from firebase_admin import firestore
from nltk.tokenize import RegexpTokenizer


# Initialising Logs
# format = "%(asctime)s: %(message)s"
# logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
# logging.info(" > Main    : Loading App ... ")

# Initialising the FireBase Client for continuously getting the state variables
# logging.info(" > Main    : Initializing Firebase connection...")
# firebase_credential = credentials.Certificate('ir-wot-certificate.json')
# firebase_app = firebase_admin.initialize_app(firebase_credential)

# Getting access to Firebase instance
# firebase_db = firestore.client()
# logging.info(" > Main    : Firebase connection initialised")


####################################3#########################################################
# 1 . Subscription to IRTestCollection on Firebase (Track Changes)
##############################################################################################
# a) For each detected change on the collection we trigger a Index update.
# b) We follow the correspondent Index Update Strategy (Incremental, Selective, MapReduce)
# c) We update the index every (X) min.


# 2. Definition of Index Data Structure
hashDoubleLinked = {}
hashRedBlackTree = {}
hashBPlusTree = {}
hashtoFirebase = {}
punctuation = '''!()-[]{};:'"\, <>./?@#$%^&*_~'''
tokenizer = RegexpTokenizer(r'\w+')


# 3. Definition of Index Metrics
stats_collection = {}
dt_index_inverter = []          # <----
t_sizes_text = []               # t - size_txt # <----
t_sizes_index = []              # t - size_index # <----


def recursive_xml_access(xml_document, path):
    if len(list(xml_document)) == 0:
        print(xml_document.tag)
        print(xml_document.text)
        # Stemming, Removing Punctuation and Tokenising ...
        # words = xml_document.text.split(' ')
        new_words = tokenizer.tokenize(xml_document.text.lower())
        # print(new_words)
        hash_word = {}
        # df_word_counts = pd.value_counts(np.array(new_words))
        # print(df_word_counts)
        for element in new_words:
            if not element in hash_word:
                hash_word[element] = [{'path': path + xml_document.tag, 'count': new_words.count(element)}]
        return hash_word
    hash_document = {}
    for child in list(xml_document):
        recursive_result = recursive_xml_access(child, path + xml_document.tag + '/')
        for key in recursive_result:
            if key in hash_document:
                hash_document[key] += recursive_result[key]
            else:
                hash_document[key] = recursive_result[key]
    return hash_document


def index_inverter(xml_document, id):
    find = False
    intermediate_document = recursive_xml_access(xml_document, '')
    for key,val in intermediate_document.items():
        score = 0
        for element in val:
            score += element['count']
        dict_dll = {id: {'score': score, 'path': intermediate_document[key]}}
        key = key.lower()
        if key in hashDoubleLinked:
            hashDoubleLinked[key].append(dict_dll)
        else:
            hashDoubleLinked[key] = dllist([dict_dll])
        # print(hashDoubleLinked)
    return


def index_inverter_to_firebase(xml_document, id, firebase_db, batch):
    find = False
    intermediate_document = recursive_xml_access(xml_document, '')
    for key,val in intermediate_document.items():
        score = 0
        for element in val:
            score += element['count']
        dict_dll = {id: {'score': score, 'path': intermediate_document[key]}}
        ###
        # Create document in Firebase with [key]
        # print("Hash: represented by Document name in Firebase")
        # print(key)
        index_hash_doc = firebase_db.collection('indexIRWoT').document(key)
        # index_hash_doc.set(dict_dll, merge=True)
        batch.set(index_hash_doc, dict_dll,merge=True)
    return


def indexer(index_structure, update_strategy, id, index_operation=None, verbose=False):
    seedURL = url_base+id
    response = requests.get(seedURL)
    response_text = response.text
    xml_document_tree = ElementTree.fromstring(response_text)
    stats_collection[id] = len(response_text.split())
    #print(response_text)
    if index_structure == 'hashddlinkedlist':
        if update_strategy == 'incremental':
            begin = time.perf_counter_ns()
            # Changing to Firebase
            index_inverter_to_firebase(xml_document_tree, id)
            end = time.perf_counter_ns()
            # print((end-begin),begin, end)
            size__text = sys.getsizeof(response_text) # <- size in memory
            size_hashDoubleLinked = memObj.total_size2(hashDoubleLinked) # <- size in memory
            if verbose:
                print(id)
                print(f'size response_text = {size__text} bytes')
                print(f'size hashDoubleLinked = {size_hashDoubleLinked} bytes')
                print(hashDoubleLinked)
            return (end-begin), size__text, size_hashDoubleLinked
        elif update_strategy == 'selective':
            pass
    elif index_structure == 'hashb+tree':
        if update_strategy == 'incremental':
            pass
        elif update_strategy == 'selective':
            pass
    elif index_structure == 'hashredblack':
        if update_strategy == 'incremental':
            pass
        elif update_strategy == 'selective':
            pass


url_base = "https://sim-wot-ugr.ue.r.appspot.com/api/smartsubspaces?output=xml&id="


def experiment1(c):
    # Number of XML Documents to be indexed
    k = c

    # Seed Id for XML Type of Documents
    izn_number = 1
    ssp_number = 1
    sss_number = 1
    vth_number = 1
    vsn_number = 1

    # Initialising the Time nS Counter
    begin = time.perf_counter_ns()
    t_sizes_text.append([begin, 0])
    t_sizes_index.append([begin, 0])

    for i in range(k):

        n = sss_number + i
        if n < 10:
            id = f'sss000{n}'
        elif 10 <= n < 100:
            id = f'sss00{n}'
        elif 100 <= n < 1000:
            id = f'sss0{n}'
        elif n<10000:
            id = f'sss{n}'
        else:
            id = 0

        delta, size_text, size_hashDoubleLinked = indexer('hashddlinkedlist', 'incremental', id, verbose=False)
        end = time.perf_counter_ns() # <----

        dt_index_inverter.append(delta) # <----
        t_sizes_text.append([end, size_text]) # <----
        t_sizes_index.append([end, size_hashDoubleLinked]) # <----
        # print("delta = ",delta, "\nsize_text = ", size_text, "\nsize_hashDoubleLinked = ", size_hashDoubleLinked)
    return dt_index_inverter, t_sizes_text, t_sizes_index


#def exp2(t_sim=100, num_ent=10, index_type=(hashddlinkedlist,hashb+tree), ):
    # exp3 ???? Numero de Eventos????
    # creacion del indice
    #for --> n= numero de entidades de simulacion

    #    Lectura desde Firebase
    #    Estadisticas de creacion en el indice se mantienen
    # ejecutar la consulta
    #for --> m = numero de palabras en la consulta =(2, 3, 5, 10, 15, ) (50, ) (100, )
    #    generar n palabras de consulta aletorias (tomadas desde el indice)
    #    tiempo de consulta hasta Resultados
        #(. X Calidad de Recuperación | Eficiencia)
#    return


def get_hashDoubleLinked(nDocs):
    exp1(nDocs)
    return hashDoubleLinked, stats_collection

#print(exp1(2))
#relv = relevancy.relevance("Dels Things same", hashDoubleLinked, stats_collection, "BM25")
#print(relv)
#print("delta = ",delta, "\nsize_text = ", size_text, "\nsize_hashDoubleLinked = ", size_hashDoubleLinked)
"""for item,val in hashDoubleLinked.items():
    print("=> ",item)
    for item2 in val.iternodes():
        for item3, val3 in item2.value.items():
            print(item3, val3['score'])"""


def indexCreationRoutine(index_structure, update_strategy, collection_pipeline, firebase_db, batch, index_operation=None, verbose=False):
    stats_N = 0
    if index_structure == 'hashddlinkedlist':
        if update_strategy == 'incremental':
            for seedURL in collection_pipeline:
                response = requests.get(seedURL)
                response_text = response.text
                xml_document_tree = ElementTree.fromstring(response_text)
                stats_N += 1
                stats_collection[seedURL] = len(response_text.split())
                index_inverter(xml_document_tree, seedURL)
    if index_structure == 'hashtofirebase':
        if update_strategy == 'incremental':
            for seedURL in collection_pipeline:
                response = requests.get(seedURL)
                response_text = response.text
                # print(response_text)
                xml_document_tree = ElementTree.fromstring(response_text)
                stats_N += 1
                # print(stats_N)
                stats_collection[seedURL] = len(response_text.split())
                index_inverter_to_firebase(xml_document_tree, seedURL, firebase_db, batch)

    print("Writing to Index Firebase with Batch = ...")
    batch.commit()
    print(stats_N)

    # print("Key Stats = ...")
    index_stats_doc = firebase_db.collection('indexStats').document('Stats')
    index_stats_doc.set(stats_collection, merge=True)


    # Gathering "index_stats" as the total number of words within each of the XML Documents in the collection
    collection_stats_ref = firebase_db.collection("indexStats").document("Stats")
    stats_doc = collection_stats_ref.get()
    index_stats = stats_doc.to_dict()
    stats_N = len(index_stats)
    index_stats_n = firebase_db.collection('indexStats').document('DocN')
    index_stats_n.set({'N': stats_N}, merge=True)

    return stats_collection, stats_N, xml_document_tree, hashDoubleLinked


# Collection Pipeline is the List of URLS to be indexed .... as an Example
# collection_pipeline = ["https://sim-wot-ugr.ue.r.appspot.com/api/v2/virtualspaces?output=xml&id=IZN00000001",
#                       "https://sim-wot-ugr.ue.r.appspot.com/api/v2/virtualspaces?output=xml&id=IZN00000002",
#                        "https://sim-wot-ugr.ue.r.appspot.com/api/v2/virtualspaces?output=xml&id=SSP00000001"]


def index_api_request(collection_pipeline, firebase_db):
    batch = firebase_db.batch()
    stats, N, xml_doc, index = indexCreationRoutine('hashtofirebase', 'incremental', collection_pipeline, firebase_db, batch)
    return "{'index-result': 'successfully Indexed', 'N': N}"

