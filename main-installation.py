import segment.analytics as analytics
import os
import logging
import datetime
import yaml
import json

def check_cluster_monitoring_config():
    with open("config.yaml") as stream:
        try:
            config = yaml.safe_load(stream)
            if 'telemeterClient' in config:
                if 'enabled' in config['telemeterClient']:
                    if config['telemeterClient']['enabled'] == "False" or config['telemeterClient']['enabled'] == "false":
                        return 1
        except yaml.YAMLError as exc:
            print(exc)
    return 0

if check_cluster_monitoring_config() == 1:
    print("TelemeterClient have been disabled via the cluster-monitoring-config")
    return

def on_error(error, items):
    print("An error occurred:", error)

logging.getLogger('segment').setLevel('DEBUG')

analytics.write_key = 'jwq6QffjZextbffljhUjL5ODBcrIvsi5'

f = open('ingestion.json')
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


