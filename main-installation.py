import segment.analytics as analytics
import os
import logging
import re
import json

logging.getLogger('segment').setLevel('DEBUG')

def on_error(error, items):
    print("An error occurred:", error)

analytics.write_key = 'jwq6QffjZextbffljhUjL5ODBcrIvsi5'

f = open('ingestion.json')
data = json.load(f)

    # analytics.debug = True
analytics.on_error = on_error
analytics.track(
    data["user_id"], 
    'New Install', 
    {
        'cluster': data["cluster"]
    },
    {
        'groupId': data["org_id"],
    }
)
analytics.flush()

