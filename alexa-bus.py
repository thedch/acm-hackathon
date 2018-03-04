from __future__ import print_function
import requests
import json
import googlemaps
import auth

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}

    card_title = "Welcome"

    # r = requests.get("https://danielhunter.io/static/README.txt")
    # speech_output = r.text

    speech_output = "Welcome the Santa Cruz Slug Bus App! I can help you " \
                    "get to class on time. Where do you want to go? " \

    # speech_output = '<speak> ' + speech_output + ' </speak>'

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Sorry, I didn't understand. Where do you " \
                    "want to go?"

    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for Santa Cruz Slug Bus App! " \
                    "Have a nice day!"

    # speech_output = '<speak> ' + speech_output + ' </speak>'

    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def newBusRoute(intent, session, address):
    session_attributes = {}
    reprompt_text = None
    should_end_session = True
    destination = "UCSC " + intent['slots']['Destinations']['value']
    arrival_time = intent['slots']['ArrivalTime']['value']

    print(arrival_time)

    gmaps = googlemaps.Client(key=auth.key)

    r = gmaps.directions(address,
                         destination,
                         mode="transit")

    steps = r[0]['legs'][0]['steps']

    for step in steps:
        if step['travel_mode'] == 'TRANSIT':
            firstBusStep = step

    print('Bus number: ', firstBusStep['html_instructions'])

    busNumber = firstBusStep['html_instructions'].split()[2]

    # arrival_time = '<say-as interpret-as="time">' + arrival_time + '</say-as> '

    speech_output = 'To get to destination by ' + arrival_time

    speech_output += 'Take the ' + busNumber + ' '
    # speech_output += '<p> Take the ' + busNumber + '</p>'
    speech_output += 'Starting from ' + address + '... '
    speech_output += 'Get on at ' + firstBusStep['transit_details']['departure_stop']['name'] + '... '
    # speech_output += 'Get off at ' + firstBusStep['transit_details']['arrival_stop']['name'] + '... '
    # speech_output += 'Bus Leaves at ' + firstBusStep['transit_details']['departure_time']['text'] + '... '
    # speech_output += 'You will arrive at ' + firstBusStep['transit_details']['arrival_time']['text']

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.

    # speech_output = '<speak> ' + speech_output + ' </speak>'

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """
    return

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    # print("on_launch requestId=" + launch_request['requestId'] +
          # ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()

def errorMessage(intent, session):
    session_attributes = {}
    reprompt_text = None
    should_end_session = False
    speech_output = 'Could not find your location, make sure that proper permissions are set for slug bus finder in the alexa amazon mobile app'

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

def on_intent(event):
    """ Called when the user specifies an intent for this skill """

    # print("on_intent requestId=" + intent_request['requestId'] +
          # ", sessionId=" + session['sessionId'])


    intent_request = event['request']
    session = event['session']

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "NewBusRouteIntent":
        address, error = getAddress(event)
        if error:
            return errorMessage(intent, session)
        return newBusRoute(intent, session, address)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def getAddress(event):
    ''' Returns the address of the user if the application has sufficient permissions
    Else, returns an empty string and boolean 'True' to indicate error

    Return type: Tuple
    '''
    deviceID = event['context']['System']['device']['deviceId']
    bearer = event['context']['System']['apiAccessToken']
    endpoint = event['context']['System']['apiEndpoint']

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + bearer,
    }

    r = requests.get(endpoint + '/v1/devices/' + deviceID + '/settings/address', headers=headers)

    if r.status_code != 200:
        return '', True

    line1 = r.json()['addressLine1']
    city = r.json()['city']

    address = line1 + ' ' + city

    return address, False

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    # print("on_session_ended requestId=" + session_ended_request['requestId'] +
          # ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """

    # print("event.session.application.applicationId=" +
          # event['session']['application']['applicationId'])


    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event)
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
