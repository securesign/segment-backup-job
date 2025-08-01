#!/usr/bin/python
from kubernetes import client, config
import yaml
from openshift.dynamic import DynamicClient
import time
import json
import os
import requests
from nightly import main_nightly
from installation import main_installation

def openshift_setup():
    try:
        config.load_incluster_config()
        print("Using in-cluster configuration.")
    except config.ConfigException:
        try:
            config.load_kube_config()
            print("Using kubeconfig file.")
        except config.ConfigException:
            raise RuntimeError("Could not load in-cluster or kubeconfig configuration.")
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
        print('Could not get configmap cluster-monitoring-config in openshift-monitoring namespace, and thus it cannot have `.telemeterClient.disabled: true`. Continuing ...')
        return 0

def check_thanos_querier_status(query_url, bearer_token, REQUESTS_CA_BUNDLE, REQUESTS_CA_BUNDLE_INTERNAL):
    attempt = 0
    attempts = 30
    sleep_interval = 5

    headers = {'Authorization': '{bearer_token}'.format(bearer_token=bearer_token)}
    while attempt < attempts:
        try:
            response = fetch_response_data(query_url+"/api/v1/status/buildinfo", headers, REQUESTS_CA_BUNDLE, REQUESTS_CA_BUNDLE_INTERNAL)
            print(response)
            if response.status_code == 200 or response.status_code == 201:
                return True
            else:
                print('API is not accessible yet. Retrying in ', sleep_interval, ' seconds...')
            attempt = attempt + 1
            time.sleep(sleep_interval)
        except requests.exceptions.RequestException as e:
            print(f"Request failed with error: {e}")
            attempt = attempt + 1
            time.sleep(sleep_interval)
    
    print('Timed out. Thanos Querier API did not respond in the configured URL.')
    return False

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
        print('Could not get ConfigMap `cluster-monitoring-config` in namespace `openshift-monitoring`, meaning userWorkloadMonitoring is not enabled or there are permissions errors.')
        return 1
    
def get_bearer_token():
    api_client = client.ApiClient()
    configuration = api_client.configuration

    bearer_token = configuration.api_key.get('authorization')

    if not bearer_token:
        raise RuntimeError("Bearer token not found in the loaded configuration.")

    return bearer_token

def write_dict_as_json(dictionairy):
    json_object = json.dumps(dictionairy, indent=4)
    with open('./ingestion.json', 'w+') as outfile:
        outfile.write(json_object)
        outfile.close()

def fetch_response_data(query_url, headers, REQUESTS_CA_BUNDLE, REQUESTS_CA_BUNDLE_INTERNAL):
    try:
        response = requests.get(query_url, headers=headers, verify=REQUESTS_CA_BUNDLE)
    except:
        response = requests.get(query_url, headers=headers, verify=REQUESTS_CA_BUNDLE_INTERNAL)
    return response

def query_nightly_metrics(openshift_client, thanos_quierier_host, bearer_token, base_domain, REQUESTS_CA_BUNDLE, REQUESTS_CA_BUNDLE_INTERNAL):
    fulcio_new_certs=None
    rekor_new_entries=None
    rekor_qps_by_api=None

    fulcio_new_certs_query_data='query=fulcio_new_certs'
    fulcio_new_certs_query_URL = '{thanos_quierier_host}/api/v1/query?&{fulcio_new_certs_query_data}'.format(thanos_quierier_host=thanos_quierier_host, fulcio_new_certs_query_data=fulcio_new_certs_query_data)
    rekor_new_entries_query_data='query=rekor_new_entries'
    rekor_new_entries_query_URL = '{thanos_quierier_host}/api/v1/query?&{rekor_new_entries_query_data}'.format(thanos_quierier_host=thanos_quierier_host, rekor_new_entries_query_data=rekor_new_entries_query_data)
    rekor_qps_by_api_query_data='query=rekor_qps_by_api'
    rekor_qps_by_api_query_URL='{thanos_quierier_host}/api/v1/query?&{rekor_qps_by_api_query_data}'.format(thanos_quierier_host=thanos_quierier_host, rekor_qps_by_api_query_data=rekor_qps_by_api_query_data)
    headers = {'Authorization': '{bearer_token}'.format(bearer_token=bearer_token)}

    fulcio_new_certs_response_data = fetch_response_data(fulcio_new_certs_query_URL, headers, REQUESTS_CA_BUNDLE, REQUESTS_CA_BUNDLE_INTERNAL)
    if fulcio_new_certs_response_data.status_code == 200 or fulcio_new_certs_response_data.status_code == 201:
        fulcio_new_certs_json = fulcio_new_certs_response_data.json()
        if fulcio_new_certs_json['status'] == 'success' and  fulcio_new_certs_json['data']['result']:
            fulcio_new_certs = fulcio_new_certs_json['data']['result'][0]['value'][1]

    rekor_new_entries_response_data = fetch_response_data(rekor_new_entries_query_URL, headers, REQUESTS_CA_BUNDLE, REQUESTS_CA_BUNDLE_INTERNAL)
    if rekor_new_entries_response_data.status_code == 200 or rekor_new_entries_response_data.status_code == 201:
        rekor_new_entries_json = rekor_new_entries_response_data.json()
        if rekor_new_entries_json['status'] == 'success' and rekor_new_entries_json['data']['result']:
            if len(rekor_new_entries_json['data']['result']) == 0:
                rekor_new_entries = 0
            else:
                rekor_new_entries = rekor_new_entries_json['data']['result'][0]['value'][1]

    rekor_qps_by_api_response_data = fetch_response_data(rekor_qps_by_api_query_URL, headers, REQUESTS_CA_BUNDLE, REQUESTS_CA_BUNDLE_INTERNAL)
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

    RUN_TYPE = os.environ.get('RUN_TYPE')
    if RUN_TYPE is not None:
        print('running in mode: ', RUN_TYPE)
    else:
        print('RUN_TYPE has not be set, job will fail.')
        exit(1)

    base_domain = os.environ.get('BASE_DOMAIN')
    if base_domain is None:
        print('failed to get base_domain which is required for both installation and nightly metrics. Failing job.')
        exit(1)

    if RUN_TYPE == 'nightly':
        requests_ca_bundle_internal = os.environ.get('REQUESTS_CA_BUNDLE_INTERNAL')
        requests_ca_bundle = os.environ.get('REQUESTS_CA_BUNDLE')

        user_workload_monitoring_status = check_user_workload_monitoring(openshift_client)
        if user_workload_monitoring_status == 1:
            print('userWorkloadMonitoring is a requirement for nightly metrics. Failing job.')
            exit(0)

        bearer_token = get_bearer_token()
        if bearer_token == 1:
            print('failed to retrieve the service Account bearer token which is required for nightly metrics. Failing job.')
            exit(1)

        thanos_querier_url = os.environ.get('THANOS_QUERIER_URL', "https://thanos-querier.openshift-monitoring.svc:9091")
        thanos_status = check_thanos_querier_status(thanos_querier_url, bearer_token, requests_ca_bundle, requests_ca_bundle_internal)
        if not thanos_status:
            print('thanos-querier is not up and is a dependency of nightly metrics. Failing job.')
            exit(1)

        query_nightly_metrics(openshift_client, thanos_querier_url, bearer_token, base_domain, requests_ca_bundle, requests_ca_bundle_internal)
        main_nightly()

    elif RUN_TYPE == 'installation':
        metrics_dict = { 'base_domain': base_domain}
        write_dict_as_json(metrics_dict)
        main_installation()

main()
