import sys
sys.setrecursionlimit(1500)

import firebase_admin
import requests
import xml.etree.ElementTree as ElementTree

# Libraries for Data Structures
from pyllist import dllist
from bplustree import BPlusTree
import red_black_dict_mod
import time
from urllib.parse import urlparse, parse_qs

# Creation of the Data Structure
hashDoubleLinked = dllist()
#hashBPlusTree = BPlusTree('./b_plus_file', order=2)
#hashRedBlackTree = red_black_dict_mod.RedBlackTree()

from firebase_admin import credentials
from firebase_admin import firestore

# Initialising the FireBase Client for continuously getting the state variables
firebase_credential = credentials.Certificate('ir-wot-ugr-certificate.json')
firebase_admin.initialize_app(firebase_credential)
firebase_db = firestore.client()
id_simu = ''
start = ''
end = ''

# IR.WoT Crawler Seed
#seedURL = "https://sim-wot-ugr.ue.r.appspot.com/api/smartsubspaces?output=xml&id=sss0057"
#xml_document = requests.get(seedURL)
# print(xml_document.content)
#xml_document = ElementTree.fromstring(xml_document.content)
#print(xml_document)


#
hash_map = {}


def recursive_xml_access(xml_document, path):
    if len(xml_document.getchildren()) == 0:
        word = xml_document.text.split(' ')
        hash_word = {}
        for element in word:
            if not element in hash_word:
                hash_word[element] = [{'path': path + xml_document.tag, 'count': xml_document.text.count(element)}]
        return hash_word
    hash_document = {}
    for child in xml_document.getchildren():
        recursive_result = recursive_xml_access(child, path + xml_document.tag + '/')
        for key in recursive_result:
            if key in hash_document:
                hash_document[key] += recursive_result[key]
            else:
                hash_document[key] = recursive_result[key]
    return hash_document

def delete_from_index(id, structure):
    if structure == 'hash_double_linked_list':
        for value in hashDoubleLinked:
            if value['ngram'] == id:
                hashDoubleLinked.remove(value)

def index_inverter(xml_document, id, structure):
    intermediate_document = recursive_xml_access(xml_document, '')
    for key in intermediate_document:
        dict_dll = {'ngram':key}
        dict_rbt = {}
        score = 0
        for element in intermediate_document[key]:
            score += element['count']
        index = 0
        flag = False
        for value in hashDoubleLinked:
            if value['ngram'] == key:
                dict_dll = value
                dict_dll[id] = {'score': score, 'path': intermediate_document[key]}
                flag = True
            if not flag:
                index += 1

        if structure == 'hash_double_linked_list':
            if flag:
                node = hashDoubleLinked.nodeat(index)
                hashDoubleLinked.remove(node)
            dict_dll[id] = {'score': score, 'path': intermediate_document[key]}
            hashDoubleLinked.append(dict_dll)

        if structure == 'hash_red_black_tree':
            flag = False
            try:
                if hashRedBlackTree.find(key):
                    dict_rbt = hashRedBlackTree.find(key)
                    flag = True
                dict_rbt[id] = {'score': score, 'path': intermediate_document[key]}
                hashRedBlackTree.add(key, dict_rbt)
            except Exception as e:
                print(e)


def bm25(q, k1, k3, b, dl, avgdl, index):

    sim = 0
    arr = {}
    for word in q.split(' '):
        if word in arr:
            arr[word] += 1
        else:
            arr[word] = 1
    max_el = []
    max_score = 0
    for item in index:
        sim = 0
        for word in arr:
            if word in item[2] :
                tfd = item[2][word]
                tfq = arr[word]
                r = 1
                R = 1
                n = 2
                N = 2
                K = k1 * ((1 - b) + b * dl / avgdl)
                sim += math.log(((r + 0.5) / (R - r + 0.5)) / ((n - r + 0.5) / (N - n - R + r + 0.5))) * (
                            ((k1 + 1) * tfd) / (K + tfd)) * (((k3 + 1) * tfq) / (k3 + tfq))
        if sim > max_score:
            max_score = sim
            max_el = item
    return max_el


i = 0
j = 0
sim_times_add = []
sim_times_deletion = []
def firebase_snapshot(collect_snapshot, changes, read_time):
    global i
    global j
    global id_simu
    global start
    global end
    global sim_times_add
    global sim_times_deletion
    print('Firebase subscription... to Crawler Pipe')
    for change in changes:
        if change.type.name == 'ADDED':
            crawler_wot_change_doc = change.document.to_dict()
            if crawler_wot_change_doc['changeType'] == 'create':
                if id_simu != crawler_wot_change_doc['id']:
                    j = 0
                    sim_times_add = []
                    sim_times_deletion = []
                    id_simu = crawler_wot_change_doc['id']
                    start = time.time()
                seedURL = crawler_wot_change_doc['URL']
                xml_document = requests.get(seedURL)
                if xml_document.status_code == 200:
                    xml_document = ElementTree.fromstring(xml_document.content)
                    ###
                    # Inversion of the Index
                    ###
                    if j > crawler_wot_change_doc['limitEntities']:
                        start_addition = time.time()
                        index_inverter(xml_document, crawler_wot_change_doc['URL'][-7:],crawler_wot_change_doc['index_structure'])
                        end_addition = time.time()
                        sim_times_add.append(end_addition - start_addition)
                        print('sim addition:::')
                        print(sim_times_add)
                    else:
                        index_inverter(xml_document, crawler_wot_change_doc['URL'][-7:],
                                       crawler_wot_change_doc['index_structure'])
                    j += 1
                    if j == crawler_wot_change_doc['limitEntities']:
                        end = time.time()
                        structure_type = crawler_wot_change_doc['index_structure']
                        size = 0
                        if structure_type == 'hash_double_linked_list':
                            for el in hashDoubleLinked:
                                size += sys.getsizeof(el)
                        elif structure_type == 'hash_red_black_tree':
                            size = 0

                        print('time:::')
                        print(end - start)
                        print('size:::')
                        print(size)
                    #print(hashDoubleLinked)
                    # CHECK! RED BLACK TREE
            elif crawler_wot_change_doc['changeType'] == 'delete':
                seedURL = crawler_wot_change_doc['URL']
                parsed = urlparse(seedURL)
                id_query = parse_qs(parsed.query)['id'][0]
                print('idddd::::')
                print(id_query)
                start_delete_time = time.time()
                delete_from_index(id_query, crawler_wot_change_doc['index_structure'])
                end_delete_time = time.time()
                sim_times_deletion.append(end_delete_time - start_delete_time)
                print('sim deletion:::')
                print(sim_times_deletion)
            firebase_db.collection('crawlerPipe').document(change.document.id).delete()
    return


def search(structure, query_size):


def firebase_snapshot_experiment(collect_snapshot, changes, read_time):
    print('Firebase subscription... to Experiment Pipe')
    for change in changes:
        if change.type.name == 'ADDED':
            crawler_wot_change_doc = change.document.to_dict()
            structure = crawler_wot_change_doc['index_structure']

            print('search ......')


# Subscription to Firestore: simSettings Control Variables
firebase_db.collection('crawlerPipe').on_snapshot(firebase_snapshot)
firebase_db.collection('experimentPipe').on_snapshot(firebase_snapshot_experiment)
while True:
    i = 0
