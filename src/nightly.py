import segment.analytics as analytics
import os
import logging
import json
import yaml

def on_error(error, items):
    print("An error occurred:", error)

def main_nightly():
    logging.getLogger('segment').setLevel('DEBUG')

    analytics.write_key = 'jwq6QffjZextbffljhUjL5ODBcrIvsi5'

    integrations={
    'cdnURL': 'console.redhat.com/connections/cdn',
    'Segment.io': {
        'apiHost': 'console.redhat.com/connections/api/v1',
        'protocol': 'https'
    }
    }
    f = open('ingestion.json')
    data = json.load(f)


    body_dict={
        'fulcio_new_certs': data["fulcio_new_certs"],
        'rekor_new_entries': data["rekor_new_entries"],
        'rekor_qps_by_api': data["rekor_qps_by_api"],
    }

    # analytics.debug = True
    analytics.track(
        data["base_domain"], 
        'Nightly Usage Metrics', 
        body_dict,
        integrations=integrations
    )
    analytics.flush()