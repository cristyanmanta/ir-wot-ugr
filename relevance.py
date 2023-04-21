import datetime
import math

def get_tfq(query):
    arr = {}
    for word in query.split(' '):
        if word in arr:
            arr[word] += 1
        else:
            arr[word] = 1
    return arr


def BM25_core(tfd, tfq, dl, avgdl, N, verbose=False, k1=1.2, k3=1.2, b=0.75 ):
    if verbose: print("BM25_2:  \ttfd = ", tfd, "\ttfq = ", tfq, "\tdl = ", dl, "\tavgdl = ", avgdl, "\tN = ",N)
    # tfd frequency of term t in document d
    # tfq frequency of term t in the query q ===
    # fqi is the number of documents that contain term t
    # IDF_qi_a = math.log(1 + (N-tfq+0.5/tfq+0.5))
    return math.log(1+(N-tfq+0.5/tfq+0.5))*( ( (k1+1)*tfd )/( k1*( (1-b) + b*(dl/avgdl) ) + tfd ))*( ( (k3+1)*tfq )/( k3 + tfq) )


def BM25(dict_tfq, index_ref, stats_collection, N, verbose=False):
    """
    dict_tfd = {
        term1: {
            name_document1: frequency_term1_in_document1,
            name_document2: frequency_term1_in_document2,
            ...
        },
        term2: {
            name_document1: frequency_term2_in_document1,
            name_document2: frequency_term2_in_document2,
            ...
        },
        ...
    }
    """
    docs = {}               # name_document: length_document
    dict_avgdl = {}         # dict => term: length_average_documents_with_term
    dict_tfd = {}           # dict => term: { name_document: frequency_term_in_document, ... }
    paths = {}
    sumdl = 0
    for doc, dl in stats_collection.items():
        sumdl += dl
    avgdl = sumdl/N
    for term, tfq in dict_tfq.items():
        docs_tfd_dl = {}    # dict => name_document: [frequency_t_in_document, length_document]
        # Querying the index for posing list about terms
        term_ref = index_ref.collection("indexIRWoT").document(term)
        term_posting_doc = term_ref.get()
        if term_posting_doc.exists:
            term_posting_list = term_posting_doc.to_dict()
            # print("Index Posting Lists:")
            # print(term_posting_list)
            for key in term_posting_list:
                # print("Data within Posting Lists")
                # print(key)
                doc_name = key
                score = term_posting_list[key]['score']
                # print("Score is:")
                # print(score)
                paths_arr = term_posting_list[key]['path']
                dl = stats_collection[key]
                docs_tfd_dl[key] = score
                docs[key] = dl
                if doc_name in paths:
                    paths[doc_name].update({term: paths_arr})
                else:
                    paths[doc_name] = {term: paths_arr}
        else:
            None
        dict_avgdl[term] = avgdl/N
        dict_tfd[term] = docs_tfd_dl
    if verbose: 
        # print("doc_name: dl\n",docs)
        # print("ngram: { doc_name: score }\n",dict_tfd)
        # print("ngram: avgdl\n",dict_avgdl,"\n")
        None
    dict_relevancy = {}
    if docs:
        for doc, dl in docs.items():
            BM25_score = 0
            for term, dict_docs in dict_tfd.items():
                if dict_docs.get(doc):
                    tfd = dict_docs[doc]
                else:
                    tfd = 0
                fqi = len(dict_docs)
                if verbose: print("term: ", term, "\tdoc: ", doc)
                BM25_score += BM25_core(tfd, fqi, dl, avgdl, N, verbose)
            # dict_relevancy[doc] = BM25_score
            # print("Ordering Paths ... and Summing Up ... ")
            # print(paths[doc])
            new_paths = {}
            sum_counts = 0
            for term in paths[doc].items():
                # print(term[1])
                for count in term[1]:
                    # print(count["path"] + ": " + str(count["count"]))
                    if count["path"] in new_paths.keys():
                        new_paths[count["path"]] = new_paths[count["path"]] + count["count"]
                    else:
                        new_paths[count["path"]] = count["count"]
            # Ordering the Paths by counts
            #
            # print("Checking ... ")
            # print(new_paths)
            sorted_paths = sorted(new_paths.items(), key=lambda x: x[1], reverse=True)
            converted_paths = dict(sorted_paths)
            # print(converted_paths)

            # Gathering friendly-name and location of Things!
            # print("Friendly-name and Location ... ")
            doc_pointer = doc[len(doc) - 11:]
            doc_ref = index_ref.collection("IRTestCollection").document(doc_pointer)
            name_fiendly_field = doc_ref.get(field_paths={'name_friendly'})
            name_fiendly_dict = name_fiendly_field.to_dict()
            # print(name_fiendly_dict)
            properties_field = doc_ref.get(field_paths={'properties'})
            properties_dict = properties_field.to_dict()
            latitude_field = round(properties_dict['properties']['latitude'], 4)
            longitude_field = round(properties_dict['properties']['longitude'], 4)
            # Get Last Modified sub-field
            events_field = doc_ref.get(field_paths={'events'})
            events_dict = events_field.to_dict()
            if events_field == '':
                last_modified_field = datetime.datetime(2000, 1, 1)
            else:
                if events_dict == {}:
                    last_modified_field = datetime.datetime(2000, 1, 1)
                else:
                    last_modified_field = events_dict['events']['last_modified']

            # Ordering the General Results by score

            # dict_relevancy[doc] = {'score': BM25_score, 'path': paths[doc]} --> V1

            dict_relevancy[doc] = {'score': BM25_score, 'path': converted_paths,
                                   'name_friendly': name_fiendly_dict['name_friendly'],
                                   'geo_location': [latitude_field, longitude_field],
                                   'last_modified': last_modified_field}
            sorted_dict_relevancy = sorted(dict_relevancy.items(), key=lambda x: x[1]["score"], reverse=True)
            converted_dict_relevancy = dict(sorted_dict_relevancy)
    else:
        converted_dict_relevancy = {}
        print("Error Handling ... Your search - did not match any documents.")
    return converted_dict_relevancy


def relevance(query, index_ref, stats_collection, N, algorithm, verbose=False):
    query = query.lower()
    dict_tfq = get_tfq(query) # dict => term: frequency_in_query
    # print(dict_tfq)
    if algorithm == "BM25":
        return BM25(dict_tfq, index_ref, stats_collection, N, verbose)


