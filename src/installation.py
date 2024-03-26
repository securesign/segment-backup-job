import segment.analytics as analytics
import os
import logging
import yaml
import json

def on_error(error, items):
    print("An error occurred:", error)

def main_installation():

    logging.getLogger('segment').setLevel('DEBUG')

    analytics.write_key = 'jwq6QffjZextbffljhUjL5ODBcrIvsi5'

    f = open('./ingestion.json')
    data = json.load(f)

    integrations={
    'cdnURL': 'console.redhat.com/connections/cdn',
    'Segment.io': {
        'apiHost': 'console.redhat.com/connections/api/v1',
        'protocol': 'https'
    }
    }

    # analytics.debug = True
    analytics.on_error = on_error
    analytics.on_error = on_error
    analytics.track(
        data["base_domain"], 
        'New Install', 
        integrations=integrations
    )
    analytics.flush()