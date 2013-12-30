from __future__ import print_function, absolute_import, division

import json

from flask import request, make_response

import twitter
import memcache

import waveplot.utils

from waveplot import app
from waveplot.passwords import passwords

def tweet_to_html(data):
    text = data['text']
    urls = data['entities'].get('urls',[])
    users = data['entities'].get('user_mentions',[])
    
    for url in urls:
        i = url['indices']
        expanded_url = url['expanded_url']
        display_url = url['display_url']
        
        text = text[:i[0]] + u'<a href=\'{}\'>{}</a>'.format(expanded_url,display_url) + text[i[1]:]
    
    for user in users:
        i = user['indices']
        name = user['name']
        text = text[:i[0]] + u'<a href=\'https://twitter.com/{0}\'><b>@{0}</b></a>'.format(name) + text[i[1]:]
        
    return text
    

@app.route('/json/tweets', methods = ['GET'])
@waveplot.utils.crossdomain(origin = '*')
def tweets():
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)
    
    results = mc.get('tweet_data')
    if results is None:
        t = twitter.Twitter(
            auth=twitter.OAuth(
                passwords['twitter']['access_token_key'],
                passwords['twitter']['access_token_secret'],
                passwords['twitter']['consumer_key'],
                passwords['twitter']['consumer_secret']
            )
        )

        statuses = t.statuses.user_timeline(screen_name="WavePlot")
    
        results = [tweet_to_html(s) for s in statuses[0:3]]
        mc.set('tweet_data', results, time=(5*60))
    
    response = make_response(json.dumps(results))
    response.mimetype = 'application/json'
    
    return response
