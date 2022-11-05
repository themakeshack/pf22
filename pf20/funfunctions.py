import json
import time

import html2text
import urllib3

from my_debug import printdebug


# Function that gets Chuck Norris jokes from the internet. It uses an HTTP GET and then a JSON parser

def getChuckNorrisQuote():
    try:
        # The database where the jokes are stored
        ICNDB = "http://api.icndb.com/jokes/random"
        http = urllib3.PoolManager(timeout=10)
        response = http.request('GET', ICNDB)
        # The response is byte encoded JSON and needs to be decoded and parsed
        # The JSON format is the following
        # {u'type': u'success', u'value' : {u'joke': 'Text of the joke', u'id': 238, u'categories': []}}
        parsed_content = json.loads(response.data.decode())
        joke = "\n\n** Random Chuck Norris Quote **:\n" + html2text.html2text(parsed_content['value']['joke'])
        # noinspection PyArgumentList
        printdebug(1, joke)
        return joke

    except:
        return "Internet not available"


# Function that gets a number trivia from the internet. It uses an HTTP GET and then a JSON parser
def getNumberTrivia():
    try:
        # The database where the trivia are stored
        NUMDB = "http://numbersapi.com/random/date?json"
        NUMDBDATEURL = "http://numbersapi.com/" + time.strftime("%m/%d", time.localtime()) + "/date?json"
        # Doing a HTTP request to get the response
        http = urllib3.PoolManager(timeout=10)
        response = http.request('GET', NUMDBDATEURL)
        # The content is byte encoded JSON and needs to be decoded and parsed
        # {u'text': u'Text of trivia', u'type' : u'trivia, u'number': <number>, u'found': True}
        parsed_content = json.loads(response.data.decode())
        trivia = "\n\n** Fact about the number " + str(parsed_content['number']) + " **\n"
        trivia = trivia + parsed_content['text']
        printdebug(1, trivia)
        return trivia
    except:
        return "Internet not available"
