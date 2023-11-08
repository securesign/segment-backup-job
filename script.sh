registry_auth=$(oc get secret pull-secret -n openshift-config -o "jsonpath={.data.\.dockerconfigjson}" | base64 -d | jq .auths."\"registry.redhat.io\"".\"auth\" | cut -d "\"" -f 2 | base64 -d)
declare org_id_index
declare user_id_index
base64_indexes=()

for ((i=0; i<${#registry_auth}; i++)); do
  char="${registry_auth:$i:1}"
  if [[ $char == "|" ]]; then
    org_id_index=$i
  elif [[ $char == ":" ]]; then
    user_id_index=$i
  elif [[ $char == "." ]]; then
    base64_indexes+=("$i")
  fi
done


org_id=${registry_auth:0:$org_id_index}
user_id=${registry_auth:$org_id_index+1:$user_id_index-($org_id_index+1)}
alg_id=$(echo ${registry_auth:$user_id_index+1:(${base64_indexes[0]}-($user_id_index+1))} | base64 -d | jq .alg | cut -d "\"" -f 2 )
sub_id=$(echo ${registry_auth:(${base64_indexes[0]}+1):(${base64_indexes[1]}-${base64_indexes[0]}-1)} | base64 -d | jq .sub |  cut -d "\"" -f 2)

TOKEN=$(oc whoami -t)
if [[ -z ${TOKEN} ]]; then
  echo "OpenShift login unsuccessful. Please try authenticating again."
  exit
fi


PROM_OCP_ROUTE=$(oc get route prometheus-k8s -n openshift-monitoring | grep -w prometheus-k8s | tr -s ' ' | cut -d " " -f2)
PROM_URL="https://${PROM_OCP_ROUTE}"

fulcio_new_certs=$(curl --globoff -s -k -X POST -H "Authorization: Bearer ${TOKEN}" \
-g "${PROM_URL}/api/v1/query" \
--data-urlencode "query=fulcio_new_certs" | \
jq -r '.data.result[] | .value[1]')

rekor_new_entries=$(curl --globoff -s -k -X POST -H "Authorization: Bearer ${TOKEN}" \
-g "${PROM_URL}/api/v1/query" \
--data-urlencode "query=rekor_new_entries" | \
jq -r '.data.result[] | .value[1]')

rekor_qps_by_api=$(curl --globoff -s -k -X POST -H "Authorization: Bearer ${TOKEN}" \
-g "${PROM_URL}/api/v1/query" \
--data-urlencode "query=rekor_qps_by_api" | \
jq -r '.data.result[] | "method:" + .metric.method + ",status_code:" + .metric.code + ",path:" + .metric.path + ",value:" + .value[1] + "|"')

echo "org_id: $org_id" > ./tmp
echo "user_id: $user_id" >> ./tmp
echo "alg_id: $alg_id" >> ./tmp
echo "sub_id: $sub_id" >> ./tmp
echo "fulcio_new_certs: $fulcio_new_certs" >> ./tmp
echo "rekor_new_entries: $rekor_new_entries" >> ./tmp
echo "rekor_qps_by_api: " $rekor_qps_by_api >> ./tmp

python3 ./main.py