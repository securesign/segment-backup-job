import segment.analytics as analytics
import os
import logging
import re
import json

# # check version
# version_file = "_version.py"
# verstr = "unknown"
# try:
#     verstrline = open(version_file, "rt").read()
# except EnvironmentError:
#     pass # Okay, there is no version file. Supports backwards compatability with old versions of the app
# else:
#     version_regex = r"^verstr = ['\"]([^'\"]*)['\"]"
#     mo = re.search(version_regex, verstrline, re.M)
#     if mo:
#         verstr = mo.group(1)
#     else:
#         print "unable to find version in %s" % (version_file,)
#         raise RuntimeError("if %s.py exists, it is required to be well-formed" % (version_file,))

# logging.info("Running segment-backup-job version:", verstr)
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

