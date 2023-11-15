import segment.analytics as analytics
import os
import logging
import datetime

logging.getLogger('segment').setLevel('DEBUG')

today = datetime.date.today()

def on_error(error, items):
    print("An error occurred:", error)

analytics.write_key = 'jwq6QffjZextbffljhUjL5ODBcrIvsi5'


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
      }
    )
    analytics.flush()

