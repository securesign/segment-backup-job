#!/usr/bin/python
from kubernetes import client, config
import yaml
from openshift.dynamic import DynamicClient
import time
import json
import base64
import os
import requests
from requests.exceptions import HTTPError
from nightly import main_nightly
from installation import main_installation

def openshift_setup():
    config.load_incluster_config()
    try:
        configuration = client.Configuration().get_default_copy()
    except AttributeError:
        configuration = client.Configuration()
    dyn_client = DynamicClient(client.ApiClient(configuration))
    return dyn_client
    

def check_cluster_monitoring_config(openshift_client):
    v1_configmaps = openshift_client.resources.get(api_version='v1', kind='ConfigMap')
    try:
        cluster_monitoring_configmap = v1_configmaps.get(name='cluster-monitoring-config', namespace='openshift-monitoring')
        if cluster_monitoring_configmap.data:
            if cluster_monitoring_configmap.data['config.yaml']:
                config_data = cluster_monitoring_configmap.data['config.yaml']
                config = yaml.safe_load(config_data)
                check_value = config.get('telemeterClient')
                if check_value is not None:
                    check_value = config.get('telemeterClient').get('enabled')
                    if check_value is not None:
                        if config.get('telemeterClient').get('enabled')  == 'False' or config.get('telemeterClient').get('enabled') == 'false' or config.get('telemeterClient').get('enabled') == False:
                            print('telemetry has been disabled')
                            return 1
                    check_value = config.get('telemeterClient').get('disabled')
                    if check_value is not None:
                        if config.get('telemeterClient').get('disabled') == 'True' or config.get('telemeterClient').get('disabled') == 'true' or config.get('telemeterClient').get('disabled') == True:
                            print('telemetry has been disabled')
                            return 1
                return 0
    except:
        print('Could not get configmap cluster-monitoring-config in openshift-monitoring namespace, and thus it cannot have \`.telemeterClient.disabled: true\`. Continuing ...')
        return 0

def check_console_operator(openshift_client):
    cluster_operator_query = openshift_client.resources.get(api_version='operator.openshift.io/v1', kind='Console')
    try:
        cluster_operator = cluster_operator_query.get(name='cluster', namespace='openshift-console')
        for annotation, value in cluster_operator['metadata']['annotations']:

            if (annotation == 'telemetry.console.openshift.io/DISABLED' or annotation == 'telemetry.console.openshift.io/disabled') and (value == True or value == 'true' or value == 'True'):
                return 1
            if (annotation == 'telemetry.console.openshift.io/ENABLED' or annotation == 'telemetry.console.openshift.io/enabled') and (value == False or value == 'false' or value == 'False'):
                return 1
        return 0
    except:
        print('could not get Console named cluster in namespace \`openshift-console\`, and thus it cannot have the disabled annotation. Continuing ...')
        return 0
        
def check_thanos_querier_status(openshift_client):
    route = openshift_client.resources.get(api_version='route.openshift.io/v1', kind='Route')
    attempt = 0
    attempts = 30
    sleep_interval = 5
    route_up = False
    thanos_quierier_host = ''

    while attempt < attempts:
        try:
            thanos_quierier_route = route.get(name='thanos-querier', namespace='openshift-monitoring')
            route_up = True
            thanos_quierier_host = thanos_quierier_route.spec.host
            break
        except:
            print('Thanos Querier route is not up yet. Retrying in ', sleep_interval, ' seconds...')
            attempt = attempt + 1
            time.sleep(sleep_interval)
    
    if route_up == True:
        return thanos_quierier_host
    elif route_up == False:
        print('Timed out. Thanos Querier route did not spin up in the \`openshift-monitoring\` namespace.')
        return 1

def check_user_workload_monitoring(openshift_client):
    v1_configmaps = openshift_client.resources.get(api_version='v1', kind='ConfigMap')
    try:
        cluster_monitoring_configmap = v1_configmaps.get(name='cluster-monitoring-config', namespace='openshift-monitoring')
        if cluster_monitoring_configmap.data:
            if cluster_monitoring_configmap.data['config.yaml']:
                config_data = cluster_monitoring_configmap.data['config.yaml']
                config = yaml.safe_load(config_data)
                check_value = config.get('enableUserWorkload')
                if check_value is None or check_value == 'false' or check_value == 'False' or check_value == False:
                    print('userWorkloadMonitoring is disabled....failing job')
                    return 1
        return 0
    except:
        print('Could not get ConfigMap \`cluster-monitoring-config\` in namespace \`openshift-monitoring\`, meaning userWorkloadMonitoring is not enabled or there are permissions errors.')
        return 1
    
def get_bearer_token():
    try:
        token_file = open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r')
        bearer_token = token_file.read().strip()
        token_file.close()
    except:
        print("Could not read the bearer token.")
        return 1
    return bearer_token

def get_sanitized_cluster_domain(openshift_client):
    route = openshift_client.resources.get(api_version='route.openshift.io/v1', kind='Route')
    try:
        openshift_console_route = route.get(name='console', namespace='openshift-console')
        sanitized_cluster_domain = openshift_console_route.spec.host[31:]
        return sanitized_cluster_domain
    except:
        print('failed to get base cluster domain.')
        return 1

def write_dict_as_json(dictionairy):
    json_object = json.dumps(dictionairy, indent=4)
    with open('./ingestion.json', 'w+') as outfile:
        outfile.write(json_object)
        outfile.close()

def query_nightly_metrics(openshift_client, thanos_quierier_host, bearer_token, base_domain):
    fulcio_new_certs=None
    rekor_new_entries=None
    rekor_qps_by_api=None
    

    fulcio_new_certs_query_data='query=fulcio_new_certs'
    fulcio_new_certs_query_URL = 'https://{thanos_quierier_host}/api/v1/query?&{fulcio_new_certs_query_data}'.format(thanos_quierier_host=thanos_quierier_host, fulcio_new_certs_query_data=fulcio_new_certs_query_data)
    rekor_new_entries_query_data='query=rekor_new_entries'
    rekor_new_entries_query_URL = 'https://{thanos_quierier_host}/api/v1/query?&{rekor_new_entries_query_data}'.format(thanos_quierier_host=thanos_quierier_host, rekor_new_entries_query_data=rekor_new_entries_query_data)
    rekor_qps_by_api_query_data='query=rekor_qps_by_api'
    rekor_qps_by_api_query_URL='https://{thanos_quierier_host}/api/v1/query?&{rekor_qps_by_api_query_data}'.format(thanos_quierier_host=thanos_quierier_host, rekor_qps_by_api_query_data=rekor_qps_by_api_query_data)
    headers = {'Authorization': 'Bearer {bearer_token}'.format(bearer_token=bearer_token)}

    fulcio_new_certs_response_data = requests.get(fulcio_new_certs_query_URL, headers=headers, verify=True,)
    if fulcio_new_certs_response_data.status_code == 200 or fulcio_new_certs_response_data.status_code == 201:
        fulcio_new_certs_json = fulcio_new_certs_response_data.json()
        if fulcio_new_certs_json['status'] == 'success' and  fulcio_new_certs_json['data']['result']:
            fulcio_new_certs = fulcio_new_certs_json['data']['result'][0]['value'][1]

    rekor_new_entries_response_data = requests.get(rekor_new_entries_query_URL,headers=headers, verify=True,)
    if rekor_new_entries_response_data.status_code == 200 or rekor_new_entries_response_data.status_code == 201:
        rekor_new_entries_json = rekor_new_entries_response_data.json()
        if rekor_new_entries_json['status'] == 'success' and rekor_new_entries_json['data']['result']:
            if len(rekor_new_entries_json['data']['result']) == 0:
                rekor_new_entries = 0
            else:
                rekor_new_entries = rekor_new_entries_json['data']['result'][0]['value'][1]


    rekor_qps_by_api_response_data = requests.get(rekor_qps_by_api_query_URL,headers=headers, verify=True,)
    if rekor_qps_by_api_response_data.status_code == 200 or rekor_qps_by_api_response_data.status_code == 201:
        rekor_qps_by_api_json = rekor_qps_by_api_response_data.json()
        if rekor_qps_by_api_json['status'] == 'success' and rekor_qps_by_api_json['data']['result']:
            rekor_qps_by_api = []
            if len(rekor_qps_by_api_json['data']['result']) > 0:
                for metric in rekor_qps_by_api_json['data']['result']:
                    metric_method = metric['metric']['method']
                    metric_code = metric['metric']['code']
                    metric_path = metric['metric']['path']
                    metric_value = metric['value'][1]
                    tmp_metric = {
                        'method': metric_method,
                        'code': metric_code,
                        'path': metric_path,
                        'value': metric_value
                    }
                    rekor_qps_by_api.append(tmp_metric)

    if fulcio_new_certs is None:
        fulcio_new_certs='null'
    if rekor_new_entries is None:
        rekor_new_entries='null'
    if rekor_qps_by_api is None:
        rekor_qps_by_api='null'

    metrics_dict = {
        'base_domain': base_domain,
        'fulcio_new_certs': fulcio_new_certs,
        'rekor_new_entries': rekor_new_entries,
        'rekor_qps_by_api': rekor_qps_by_api
    }
    write_dict_as_json(metrics_dict)

def main():
    openshift_client = openshift_setup()
    check_cluster_monitoring_config_status = check_cluster_monitoring_config(openshift_client)
    if check_cluster_monitoring_config_status == 1:
        print('gracefully terminating, telemetry explicitly disabled in cluster_monitoring_config')
        exit(0)
    check_console_operator_status = check_console_operator(openshift_client)   
    if check_console_operator_status == 1:
        print('gracefully terminating, telemetry explicitly disabled as an annotation to the Console operator')
        exit(0)
    RUN_TYPE = os.environ.get('RUN_TYPE')
    if RUN_TYPE is not None:
        print('running in mode: ', RUN_TYPE)
    else:
        print('RUN_TYPE has not be set, job will fail.')
        exit(1)
    user_workload_monitoring_status = check_user_workload_monitoring(openshift_client)
    if user_workload_monitoring_status == 1 and RUN_TYPE == "nightly":
        print('userWorkloadMonitoring is a requirement for nightly metrics. Failing job.')
        exit(0)
    thanos_quierier_host = check_thanos_querier_status(openshift_client)
    if thanos_quierier_host == 1 and RUN_TYPE == 'nightly':
        print('thanos-querier is not up and is a dependency of nightly metrics. Failing job.')
        exit(1)
    bearer_token = get_bearer_token()
    if bearer_token == 1 and RUN_TYPE == 'nightly':
        print('failed to retrieve the service Account bearer token which is required for nightly metrics. Failing job.')
        exit(1)
    base_domain = get_sanitized_cluster_domain(openshift_client)
    if base_domain == 1:
        print('failed to get base_domain which is required for both installation and nightly metrics. Failing job.')
        exit(1)
    if RUN_TYPE == 'nightly':
        query_nightly_metrics(openshift_client, thanos_quierier_host, bearer_token, base_domain)
        main_nightly()
    elif RUN_TYPE == 'installation':
        metrics_dict = { 'base_domain': base_domain}
        write_dict_as_json(metrics_dict)
        main_installation()

main()
