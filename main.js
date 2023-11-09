const fs = require('fs');
const axios = require('axios')
const write_key = 'jwq6QffjZextbffljhUjL5ODBcrIvsi5'
const_base64_wk_auth = "andxNlFmZmpaZXh0YmZmbGpoVWpMNU9EQmNySXZzaTU6Cg=="


fs.readFile("./tmp", 'utf8', (err, tmp_data) => {
    // console.log(data)
    let user = {}
    let data = {}

    let lines = tmp_data.split("\n")
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].includes("org_id:")) {
            user.org_id = lines[i].slice(8, lines[i].length)
        } else if (lines[i].includes("user_id:")) {
            user.user_id = lines[i].slice(9, lines[i].length)
        } else if (lines[i].includes("alg_id:")) {
            user.alg_id = lines[i].slice(8, lines[i].length)
        } else if (lines[i].includes("sub_id:")) {
            user.sub_id = lines[i].slice(8, lines[i].length)
        } else if (lines[i].includes("fulcio_new_certs:")) {
            data.fulcio_new_certs = lines[i].slice(18, lines[i].length )
        } else if (lines[i].includes("rekor_new_entries:")) {
            data.rekor_new_entries = lines[i].slice(17, lines[i].length)
        } else if (lines[i].includes("rekor_qps_by_api:")) {
            rekor_qps_by_api_string = lines[i].slice(16, lines[i].length - 2)
            rekor_qps_by_api_array = rekor_qps_by_api_string.split("| ")
            rekor_qps_by_api = []
            for (var j = 0; j < rekor_qps_by_api_array.length; j++) {
                api_attributes = rekor_qps_by_api_array[j].split(",")
                api_attributes_obj = {
                    'method': api_attributes[0].slice(7, api_attributes[0].length-1),
                    'status_code': api_attributes[1].slice(12, api_attributes[1].length -1),
                    'path': api_attributes[2].slice(5, api_attributes[2].length - 1),
                    'value': api_attributes[3].slice(6, api_attributes[3].length - 1)
                }
                rekor_qps_by_api.push(api_attributes_obj)
            }
            data.rekor_qps_by_api = rekor_qps_by_api
        }
    }
    console.log("data: ", typeof(data))
    let req_body = {
        "userId": user.user_id,
        "anonymousId": user.sub_id,
        "event": "Usage Metrics Nightly",
        "properties": data,
        "context": {
            "groupID": user.org_id,
        },
    }
    
    console.log(req_body)
    axios({
        method: 'post',
        url: 'https://api.segment.io/v1/track',
        data: req_body,
        headers: {
            'Content-Type': 'application/json',
            'write_key': write_key,
          }
    });
})