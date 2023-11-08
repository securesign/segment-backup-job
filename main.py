import analytics
import os

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
        if "fulcio_new_certs:" in line:
            data["fulcio_new_certs"] = line[18:len(line)-1]
        if "rekor_new_entries:" in line:
            data["rekor_new_entries"] = line[17:len(line)-1]
        if "rekor_qps_by_api:" in line:
            data["rekor_qps_by_api_string"] = line[16:len(line)-2]
            rekor_qps_by_api_string = data["rekor_qps_by_api_string"].split("| ")
            rekor_qps_by_api = []
            for api in rekor_qps_by_api_string:
                api_attributes = api.split(",")
                api_attributes_obj= {
                    'method': api_attributes[0][7:len(api_attributes[0])],
                    'status_code': api_attributes[1][12:len(api_attributes[1])],
                    'path': api_attributes[2][5:len(api_attributes[2])],
                    'value': api_attributes[3][6:len(api_attributes[3])],
                }
                rekor_qps_by_api.append(api_attributes_obj)
            
analytics.track(
  user["user_id"], 
  'Usage Metrics', 
  {
    'installation_uuid': user["sub_id"],
    'fulcio_new_certs': data["fulcio_new_certs"],
    'rekor_new_entries': data["rekor_new_entries"],
    'rekor_qps_by_api': rekor_qps_by_api,
  },
  {
    'groupId': user["org_id"],
  }
)

