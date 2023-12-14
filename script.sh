#!/bin/bash

################ SET RUN TYPE DEUBGING ################
# RUN_TYPE="installation" #debugging                  #
# RUN_TYPE="nightly" #debugging                       #
#######################################################

max_attempts=60
sleep_interval=5
# ingestion_file_path="/opt/app-root/src/ingestion.json"
ingestion_file_path="./ingestion.json"
# tmp_file_path="/opt/app-root/src/tmp.json"
tmp_file_path="./tmp.json"



check_telemetry_enabled() {
  openshift_pullsecret_exists=$(oc get secret pull-secret -n openshift-config --ignore-not-found=true)
  if [[ -n $openshift_pullsecret_exists ]]; then
    cloud_dot_openshift_cluster=$(oc get secret pull-secret -n openshift-config -o json | jq -r '.data.".dockerconfigjson"' | base64 -d | jq -r '.auths."cloud.openshift.com"')
    if [[ -n $cloud_dot_openshift_cluster ]]; then
      echo "This cluster has \`cloud.openshift.com\` pullsecret credentials, and is thus deemed a CI cluster. Exiting, analytics not meant for CI clusters"
      exit 1
    fi
  fi
  cluster_monitoring_config_exists=$(oc get configmap cluster-monitoring-config -n openshift-monitoring --ignore-not-found=true)
  if [[ -n $cluster_monitoring_config_exists ]]; then
    cluster_monitoring_configs=$(oc get configmap cluster-monitoring-config -n openshift-monitoring -o json | jq '.data."config.yaml"' | cut -d "\"" -f 2)
    echo $cluster_monitoring_configs > ./config.yaml
  fi
  openshift_console_operator=$(oc get console.operator.openshift.io cluster -o json --ignore-not-found=true)
  if [[ -n $openshift_console_operator ]]; then
    disabled_annotation_exists=$(oc get console.operator.openshift.io cluster -o json | jq -r '.metadata.annotations."telemetry.console.openshift.io/DISABLED"')
    if [[ $disabled_annotation_exists == "true" ]]; then
      echo "Console Operator has annotation for disabling telemetry. Cancelling job."
      exit 1
    fi
  fi 
  return 0
}

check_thanos_querier_status() {
  local attempts=0

  while [[ $attempts -lt $max_attempts ]]; do
    route_exists=$(oc get route thanos-querier -n openshift-monitoring --ignore-not-found=true)
    if [[ -n $route_exists ]]; then
      echo "route \"thanos-querier\" is up and running in namespace "openshift-monitoring"."
      return 0
    else
      echo "Thanos Querier route is not up yet. Retrying in $sleep_interval seconds..."
    fi
    sleep $sleep_interval
    attempts=$((attempts + 1))
  done

  echo "Timed out. Thanos Querier route did not spin up in the \"openshift-monitoring\" namespace."
  return 1
}

check_user_workload_monitoring_enabled() {
  uwm_namespace_exists=$(oc get project openshift-user-workload-monitoring --ignore-not-found=true) 
  if [[ -z $uwm_namespace_exists ]]; then
    echo "Error, project \"openshift-user-workload-monitoring\" does not exist."
    exit 1
  fi
  PROM_TOKEN_SECRET_NAME=$(oc get secret -n openshift-user-workload-monitoring | grep  prometheus-user-workload-token | head -n 1 | awk '{print $1 }')
  if [[ -z $PROM_TOKEN_SECRET_NAME ]]; then 
    echo "Error, could not find a secret for the \"prometheus-user-workload-token\" in namespace \"openshift-user-workload-monitoring\"."
    exit 1
  fi
  PROM_TOKEN_SECRET_TOKEN=$(oc get secret $PROM_TOKEN_SECRET_NAME -n openshift-user-workload-monitoring -o json | jq -r '.data.token')
  if [[ -z $PROM_TOKEN_SECRET_TOKEN || $PROM_TOKEN_SECRET_TOKEN == "null" ]]; then
    echo "Error, could not get token data for the secret for the \"prometheus-user-workload-token\" in namespace \"openshift-user-workload-monitoring\"."
    exit 1
  fi
  exit 0
}

check_pull_secret_exists() {
  local attempts=0

  while [[ $attempts -lt $max_attempts ]]; do
    pull_secret_exists=$(oc get secret pull-secret -n trusted-artifact-signer-monitoring --ignore-not-found=true)
    if [[ -n $pull_secret_exists ]]; then
      echo "secret \"pull-secret\" in namespace \"trusted-artifact-signer-monitoring\" exists, proceeding."
      return 0
    else
      echo "Waiting for secret \"pull-secret\" in namespace \"trusted-artifact-signer-monitoring\" to exist..."
      sleep $sleep_interval
      attempts=$((attempts + 1))
    fi
  done

  echo "Timed out. Cannot find secret \"pull-secret\" in namespace \"trusted-artifact-signer-monitoring\"."
  echo "Please download the pull-secret from \`https://console.redhat.com/application-services/trusted-content/artifact-signer\`
  and create a secret from it: \`oc create secret generic pull-secret -n trusted-artifact-signer-monitoring --from-file=\$HOME/Downloads/pull-secret.json\`."
  return 1
}

<<<<<<< HEAD
telemetry_disabled_message=$(check_telemetry_enabled)
if [[ $? == 1 ]]; then
  echo $telemetry_disabled_message
  exit 1
fi

check_pull_secret
check_thanos_querier_status

pull_secret_exists=$(oc get secret  pull-secret -n sigstore-monitoring --ignore-not-found=true)
=======
check_pull_secret_data() {
  pull_secret=$(oc get secret pull-secret -n trusted-artifact-signer-monitoring --ignore-not-found=true -o json)
  if [[ -n $pull_secret ]]; then
    pull_secret_userID=$(echo $pull_secret | jq '.data."pull-secret.json"')
    if [[ $pull_secret_userID == "null" ]]; then
      echo "error parsing secret \"pull-secret\" in namespace \"trusted-artifact-signer-monitoring\"": did not have property \`.data.pull-secret.json\`.
      exit 1
    fi
    exit 0
  else
    echo "No TAS pull-secret found. If you would like to send metrics or recieve support support,
      please download the pull-secret from \`https://console.redhat.com/application-services/trusted-content/artifact-signer\`.
      Then create the secret \"pull-secret\" in namespace \"trusted-artifact-signer-monitoring\" from the value:  \`oc create secret generic pull-secret -n trusted-artifact-signer-monitoring --from-file=\$HOME/Downloads/pull-secret.json\`
      "
    exit 1
  fi
}
>>>>>>> d6ec969 (safe fail for default pull-secret)

parse_string_into_array_of_objects() {
  for var in "$@"
  do
    IFS="|"
    read -a values <<< "$var"
    method="${values[0]}"
    status_code=$((${values[1]}))
    path="${values[2]}"
    value=$((${values[3]}))

    jq '.rekor_qps_by_api[.rekor_qps_by_api| length] |= . + {"path": $path, "method": $method, "status_code": $status_code, "value": $value}' \
      --arg method "$method" \
      --arg status_code "$status_code" \
      --arg path "$path" \
      --arg value "$value" $ingestion_file_path > $tmp_file_path
    jq_update_file $tmp_file_path $ingestion_file_path
  done
}
 
jq_update_file() {
  if [[ $? != 0 ]]; then
    echo "jq could not parse file" 
    exit $?
  fi
  mv $1 $2
}


pse=$(check_pull_secret_exists)
psd=$(check_pull_secret_data)
console_route=$(oc get route console -n openshift-console --ignore-not-found | grep "console-openshift-console" | awk '{print $2}')
base_domain=""
echo $console_route
if [[ -z $console_route ]]; then
  echo "local testing"
  base_domain="null"
else 
  base_domain=${console_route:31:((${#console_route}-31))}
fi

if [[ "$pse" == "1" || "$psd" == "1" ]]; then
  org_id="41414141"
  user_id="41414141"
else 
  secret_data=$(oc get secret pull-secret -n trusted-artifact-signer-monitoring -o "jsonpath={.data.pull-secret\.json}")
  org_id=$(echo $secret_data | base64 -d | jq ".orgId" | cut -d "\"" -f 2 )
  user_id=$(echo $secret_data | base64 -d  | jq ".userId" | cut -d "\"" -f 2 )
fi

# Create file with user and org data so it exists
echo $base_domain

jq -n '{"org_id": $ARGS.named["org_id"],"user_id": $ARGS.named["user_id"], "base_domain": $ARGS.named["base_domain"]}' \
  --arg org_id $org_id \
  --arg user_id $user_id \
  --arg base_domain $base_domain \
  $ingestion_file_path > $tmp_file_path
  jq_update_file $tmp_file_path $ingestion_file_path


if [[ $RUN_TYPE == "nightly" ]]; then

  uwme=$(check_user_workload_monitoring_enabled)
  tqs=$(check_thanos_querier_status)

  if [[ $uwme == 1 || $tqs == 1 ]]; then
    echo "either user-workload-monitoring is not enabled or the thanos queirier is not up. Both are required for nightly runs of SBJ."
  else 
    PROM_TOKEN_SECRET_NAME=$(oc get secret -n openshift-user-workload-monitoring | grep  prometheus-user-workload-token | head -n 1 | awk '{print $1 }')
    PROM_TOKEN_DATA=$(echo $(oc get secret $PROM_TOKEN_SECRET_NAME -n openshift-user-workload-monitoring -o json | jq -r '.data.token') | base64 -d)
    THANOS_QUERIER_HOST=$(oc get route thanos-querier -n openshift-monitoring -o json | jq -r '.spec.host')

    fulcio_new_certs_query_data=$(curl -X GET -kG "https://$THANOS_QUERIER_HOST/api/v1/query?" --data-urlencode "query=fulcio_new_certs" -H "Authorization: Bearer $PROM_TOKEN_DATA" | jq '.data.result[]' )
    if [[ -z $fulcio_new_certs_query_data ]]; then 
      echo "Error with fulcio deployment, metric does not exist."
      fulcio_new_certs="null"
    else 
      fulcio_new_certs=$(echo $fulcio_new_certs_query_data | jq '.value[1]' | cut -d "\"" -f 2 )
    fi

    jq --arg fulcio_new_certs "$fulcio_new_certs" '.fulcio_new_certs = $fulcio_new_certs' $ingestion_file_path > $tmp_file_path
    jq_update_file $tmp_file_path $ingestion_file_path

    rekor_new_entries_query_data=$(curl -X GET -kG "https://$THANOS_QUERIER_HOST/api/v1/query?" --data-urlencode "query=rekor_new_entries" -H "Authorization: Bearer $PROM_TOKEN_DATA" | jq '.data.result[]' )
    declare rekor_new_entries
    if [[ -z $rekor_new_entries_query_data ]]; then
      echo "Error with rekor deployment, metric does not exist."
      rekor_new_entries="null"
    else 
      rekor_new_entries=$(curl -X GET -kG "https://$THANOS_QUERIER_HOST/api/v1/query?" --data-urlencode "query=rekor_new_entries" -H "Authorization: Bearer $PROM_TOKEN_DATA" | jq '.data.result[] | .value[1]')
      rekor_new_entries=$(echo $rekor_new_entries | cut -d "\"" -f 2 )
    fi

    jq --arg rekor_new_entries "$rekor_new_entries" '.rekor_new_entries = $rekor_new_entries' $ingestion_file_path > $tmp_file_path
    jq_update_file $tmp_file_path $ingestion_file_path

    rekor_qps_by_api_query_data=$(curl -X GET -kG "https://$THANOS_QUERIER_HOST/api/v1/query" --data-urlencode "query=rekor_qps_by_api" -H "Authorization: Bearer $PROM_TOKEN_DATA" | jq '.data.result[]' )

    jq '.rekor_qps_by_api =[]' $ingestion_file_path > $tmp_file_path
    jq_update_file $tmp_file_path $ingestion_file_path

    if [[ -n $rekor_qps_by_api_query_data ]]; then
      # rekor_qps_by_api=$(echo $rekor_qps_by_api_query_data | jq -r '"{\"method\":\"" + .metric.method + "\",\"status_code\":" + .metric.code + ",\"path\":\"" + .metric.path + "\",\"value\":" + .value[1] + "}"')
      rekor_qps_by_api=$(echo $rekor_qps_by_api_query_data | jq -r ' .metric.method + "|" + .metric.code + "|" + .metric.path + "|" + .value[1]')
      parse_string_into_array_of_objects $rekor_qps_by_api

    fi
  fi
fi

if [[ $RUN_TYPE == "nightly" ]]; then
  python3 /opt/app-root/src/main-nightly.py
elif [[ $RUN_TYPE == "installation" ]]; then
  python3 /opt/app-root/src/main-installation.py
else 
  echo "error \$RUN_TYPE not set.
    options: \"nightly\", \"installation\""
  exit 1
fi