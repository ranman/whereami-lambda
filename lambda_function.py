from __future__ import print_function
import os

import foursquare
import arrow
import boto3
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

lex = boto3.client('lex-runtime')
line_bot_api = LineBotApi(os.getenv('LINE_TOKEN'))

client = foursquare.Foursquare(access_token=os.getenv('ACCESS_TOKEN'))


def get_loc():
    checkin = client.users.checkins(params={'limit': 1})['checkins']['items'][0]
    venue = checkin['venue']
    ts = checkin['createdAt']
    return {
        'name': venue['name'], # name
        'loc': [ # latitude and longitude
            venue['location']['lat'],
            venue['location']['lng']
        ],
        'ts': ts #when
    }


def api_handler(event, context):
    return get_loc()


def alexa_handler(event, context):
    loc = get_loc()
    msg = "Randall was last at {} {}".format(loc['name'], arrow.get(loc['ts']).humanize())
    resp = {
        'version': '1.0',
        'sessionAttributes': {},
        'response':  {
            'outputSpeech': {
                'type': 'PlainText',
                'text': msg
            },
            'card': {
                'type': 'Simple',
                'title': 'SessionSpeechlet - Randall Location',
                'content': 'SessionSpeechlet - ' + msg,
            },
            'shouldEndSession': True
        }
    }
    return resp


def lex_handler(event, context):
    loc = get_loc()
    msg = "Randall was last at {} {}".format(loc['name'], arrow.get(loc['ts']).humanize())
    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": msg
            }
        }}


def line_handler(event, context):
    print(event)
    for item in event['events']:
        response = lex.post_text(
            botName='WhereIsRandall',
            botAlias='$LATEST',
            userId=item['source']['userId'],
            inputText=item['message']['text']
        )
        print(response['message'])
        line_bot_api.reply_message(
            item['replyToken'],
            TextSendMessage(text=response['message'])
        )
    return "Success!"

event_function_map = {
    'alexa': alexa_handler,
    'lex': lex_handler,
    'api': api_handler,
    'line': line_handler
}


def lambda_handler(event, context):
    print(event)
    if 'bot' in event:
        return event_function_map['lex'](event, context)
    elif event.get('request', {}).get('type') == "IntentRequest":
        return event_function_map['alexa'](event, context)
    elif 'events' in event:
        return event_function_map['line'](event, context)
    else:
        return event_function_map['api'](event, context)
