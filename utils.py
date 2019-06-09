import os
import requests,json
from private import get_api_key, get_mongo_password, get_mongo_username
from pymongo import MongoClient
import urllib.parse as up
from datetime import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client-secret.json"

url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"

import dialogflow_v2 as dialogflow
dialogflow_session_client = dialogflow.SessionsClient()
PROJECT_ID = "placesbot-acvanx"

def sorted_by_key(elem):
    return elem.get('date')

client = MongoClient("mongodb+srv://rohangoyal2014:{}@cluster0-giaxj.mongodb.net/test?retryWrites=true&w=majority".format(up.quote(get_mongo_password())))
db = client.get_database('places')
records = db.places_data

def saveToDatabase(msg, sender):
    place = {
        'msg' : msg,
        'sender': sender,
        'date' : str(datetime.now())
    }

    records.insert_one(place)

def detect_intent_from_text(text, session_id, language_code='en'):
    session = dialogflow_session_client.session_path(PROJECT_ID, session_id)
    text_input = dialogflow.types.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.types.QueryInput(text=text_input)
    response = dialogflow_session_client.detect_intent(session=session, query_input=query_input)
    return response.query_result

def get_places(parameters):
    # print(parameters) 
    r = requests.get(url + 'query=' + parameters  +
                        '&key=' + get_api_key())

    data = dict(r.json())
    
    status = data.get('status')
    
    if status !='OK':
        return []

    results = data.get('results')

    return results

def get_photos(query):
    r = requests.get(url + 'query=' + query +
                        '&key=' + get_api_key())
    data = dict(r.json())
    print(data)
    if len(data.get('results')) == 0:
        return []
    
    photos = data.get('results')[0].get('photos')

    if len(photos) == 0:
        return []
    
    photosLinks = []
    for photo in photos:
        photoreference = photo.get('photo_reference')
        photosLinks.append('https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference='+ photoreference +'&key='+get_api_key())
        break

    return photosLinks


def fetch_reply(msg, session_id):
    try:
        response = detect_intent_from_text(msg, session_id)
        if response.intent.display_name == "get_places":
            places = get_places(msg)
            saveToDatabase(msg, session_id)
            
            if len(places) == 0:
                return 'No results Found :('
            
            result = "Here are your results:"
            for i in range(min(3,len(places))):
                place = places[i]
                name = place.get('name')
                url = 'https://maps.googleapis.com/maps/api/place/details/json?placeid='+ place.get('place_id') +'&key=' + get_api_key()
                mapsLink = dict(requests.get(url).json()).get('result').get('url')
                result+="\n\n"+ str(name)+ "\n"+str(mapsLink)
            
            return result


        elif response.intent.display_name == 'get_photos':
            saveToDatabase(msg, session_id)
            photos = get_photos(msg)
            if len(photos) == 0:
                return 'No photos found :('
            else:
                return photos
        elif response.intent.display_name == 'show_history':
            history = list(records.find({'sender':session_id}))
            for i in range(len(history)):
                history[i] = dict(history[i])
            history.sort(key= sorted_by_key,reverse=True)
            limit = min(len(history),5)
            if limit == 0:
                return "No history found:)"
            resultString="Your last {} queries are:\n".format(limit)
            for i in range(limit):
                resultString+=str(i+1)+". "+history[i].get('msg')+"\nTime:"+history[i].get('date')+"\n\n"
            return resultString
        else:
            return response.fulfillment_text
        
    except:
        return 'Sorry, we can not process your request'
