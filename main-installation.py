import segment.analytics as analytics
import os
import logging
import datetime
import yaml

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

logging.getLogger('segment').setLevel('DEBUG')

today = datetime.date.today()

def on_error(error, items):
    print("An error occurred:", error)

analytics.write_key = 'jwq6QffjZextbffljhUjL5ODBcrIvsi5'


integrations={
  'cdnURL': 'console.redhat.com/connections/cdn',
  'Segment.io': {
    'apiHost': 'console.redhat.com/connections/api/v1',
    'protocol': 'https'
  }
}

user={}
data={}

with open('./tmp', 'r') as file:
    for line in file:
        if "org_id:" in line:
            user["org_id"] = line[8:len(line)-1]
        if "user_id:" in line:
            user["user_id"] = line[9:len(line)-1]
        if "alg_id:" in line:
            user["alg_id"] = line[8:len(line)-1]
        if "sub_id:" in line:
            user["sub_id"] = line[8:len(line)-1]
    # analytics.debug = True
    analytics.on_error = on_error
    analytics.track(
      user["user_id"], 
      'New Install', 
      {
        'installation_uuid': user["sub_id"]
      },
      {
        'groupId': user["org_id"],
      },
      integrations=integrations
    )
    analytics.flush()

