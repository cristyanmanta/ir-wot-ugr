import datetime
import json
import haversine as hs

from haversine import Unit

from flask import request


#
#   IR.WoT Information Retrieval for the web of Things
#   -- Query Interpreter Module
#       -- Query Processor Sub-Module
#


def query_proc():
    # Capturing the Query Form Data (CO) and (CAS) inputs
    search_term = request.form["query"]
    spatial_req = request.form["spatial_input"]
    location_req = request.form["location_input"]
    temporal_req = request.form["temporal_input"]
    type_req = request.form["type_input"]
    property_req = request.form["property_input"]
    action_req = request.form["action_input"]
    event_req = request.form["event_input"]

    co_query = search_term
    spatial_input = spatial_req

    converted_location = json.loads(location_req)

    if converted_location["lat"] == 0 and converted_location["lng"] == 0:
        location_input = {"lat":37.197055,"lng":-3.6420602}
    else:
        location_input = converted_location

    temporal_input = temporal_req
    document_input = type_req
    cas_property = property_req
    cas_action = action_req
    cas_event = event_req
    max_results = 10

    # Natural Language to NEXI Query translation

    type_nexi_square = ""
    if type_req == "0":
        type_nexi = "*"
        type_nexi_square = "["
    elif type_req == "1":
        type_nexi = "vX[@type=´virtualSensor´ and "
    elif type_req == "2":
        type_nexi = "vX[@type=´virtualThing´ and "
    elif type_req == "3":
        type_nexi = "vX[@type=´intelligentZone´ or  @type=´smartSpace´ or @type=´smartSubSpace´ and "
    else:
        type_nexi = "Error"

    co_nexi = "about(.,co_query)"

    if spatial_req == "0":
        spatial_nexi = " and .//property/geocoordinate <= 100Mts"
    elif spatial_req == "1":
        spatial_nexi = " and .//property/geocoordinate <= 1Km"
    elif spatial_req == "2":
        spatial_nexi = " and .//property/geocoordinate <= 10Km"
    elif spatial_req == "3":
        spatial_nexi = " and .//property/geocoordinate <= 100Kms"
    elif spatial_req == "4":
        spatial_nexi = " and .//property/geocoordinate <= 1000Kms"
    else:
        spatial_nexi = ""

    if temporal_req == "0":
        temporal_nexi = " and .//event/eventTime <= 10Min"
    elif temporal_req == "1":
        temporal_nexi = " and .//event/eventTime <= 1Hour"
    elif temporal_req == "2":
        temporal_nexi = " and .//event/eventTime <= 24Hour"
    elif temporal_req == "3":
        temporal_nexi = " and .//event/eventTime <= 1Week"
    elif temporal_req == "4":
        temporal_nexi = " and .//event/eventTime <= 1Month"
    else:
        temporal_nexi = ""

    if property_req != "":
        property_nexi = "//property[about(.,cas_query)]"
    else:
        property_nexi = ""

    if action_req != "":
        action_nexi = "//action[about(.,cas_query)]"
    else:
        action_nexi = ""

    if event_req != "":
        event_nexi = "//event[about(.,cas_query)]"
    else:
        event_nexi = ""

    nexi_query = "//" + type_nexi + type_nexi_square + co_nexi + spatial_nexi + temporal_nexi + \
                 "]" + property_nexi + action_nexi + event_nexi

    query = {}
    query["co_query"] = co_query
    query["spatial_input"] = spatial_input
    query["location_input"] = location_input
    query["temporal_input"] = temporal_input
    query["document_input"] = document_input
    query["cas_property"] = cas_property
    query["cas_action"] = cas_action
    query["cas_event"] = cas_event
    query["max_results"] = max_results
    query["nexi_query"] = nexi_query

    return query


def entity_filter(results, entity_restriction):
    filtered_results = {}
    for key, value in results.items():
        if entity_restriction == "0":      # All-Types
            filtered_results = results
        elif entity_restriction == "1":    # Sensors
            if key[-11:-8] == "VSN":
                filtered_results[key] = value
        elif entity_restriction == "2":    # Things
            if key[-11:-8] == "VTH":
                filtered_results[key] = value
        else:                              # Spaces
            if key[-11:-8] == "IZN" or key[-11:-8] == "SSP" or key[-11:-8] == "SSS":
                filtered_results[key] = value
    return filtered_results


def space_filter(results, spatial_restriction, user_location):
    # print(spatial_restriction)
    # print(user_location)
    filtered_results = {}
    filtered_range = 0
    loc_user = [user_location["lat"],user_location["lng"]]

    if spatial_restriction == "0":  # Range 100mts
        filtered_range = 100
    elif spatial_restriction == "1":  # Range 1Km
        filtered_range = 1000
    elif spatial_restriction == "2":  # Range 10Km
        filtered_range = 10000
    elif spatial_restriction == "3":  # Range 100Km
        filtered_range = 100000
    elif spatial_restriction == "4":  # Range 1000Km
        filtered_range = 1000000
    else:  # Range Everywhere
        filtered_range = 100000000

    for key, value in results.items():
        loc_result = value["geo_location"]
        distance = hs.haversine(loc_result,loc_user,unit=Unit.METERS)
        if distance < filtered_range:
            filtered_results[key] = value
        else:
            None
    return filtered_results


def time_filter(results, temporal_restriction):
    # print(temporal_restriction)
    # Read HERE!!!! for each Result if not in Result read from Firebase

    filtered_results = {}
    filtered_range = 0

    if temporal_restriction == "0":  # Range 5min
        filtered_range = 5
    elif temporal_restriction == "1":  # Range 1hr
        filtered_range = 60
    elif temporal_restriction == "2":  # Range 24hr
        filtered_range = 60*24
    elif temporal_restriction == "3":  # Range 1Week
        filtered_range = 60*24*7
    elif temporal_restriction == "4":  # Range 1Month
        filtered_range = 60*24*30
    else:                              # Range Anytime
        return results

    for key, value in results.items():
        last_modified_result = value["last_modified"]
        # Timestamps differences
        query_time = datetime.datetime.now()
        delta_time = query_time - last_modified_result.replace(tzinfo=None)
        delta_time = delta_time.seconds / 60
        if delta_time < filtered_range:
            filtered_results[key] = value
        else:
            None
    return filtered_results
