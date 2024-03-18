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


body_dict={
    'fulcio_new_certs': data["fulcio_new_certs"],
    'rekor_new_entries': data["rekor_new_entries"],
    'rekor_qps_by_api': data["rekor_qps_by_api"],
}
    # analytics.debug = True
analytics.on_error = on_error       
analytics.track(
    data["cluster"], 
    'Nightly Usage Metrics', 
    body_dict,
)
analytics.flush()

