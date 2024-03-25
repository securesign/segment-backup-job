

### Development

This is the script I used to automate my builds (OSX only but i guess some linux compatability):

```bash
# If https://github.com/securesign/sigstore-ocp/pull/81/files is not merged you will need to create the pull secret, go here: https://console.redhat.com/application-services/trusted-content/artifact-signer and download it
kubectl create secret generic pull-secret -n sigstore-monitoring --from-file=$HOME/Downloads/pull-secret.json

# was developing and pushing images here to test: https://quay.io/repository/grpereir/segment-backup-job?tab=tags, get the latest tag and set version to be 1 after that

#Example version value
export version=25

export segment_backup_job_repo_path=$(pwd) #if your working from another directory swap this value out
export sigstore_ocp_path="" # Set absolute path to sigstore-ocp, used for automating editing of the values file

# my podman is broken due to QEMU issues (run mv Containerfile Dockerfile once)
podman build $segment_backup_job_repo_path --platform=linux/amd64 -t quay.io/grpereir/segment-backup-job:1.0.$version
podman push quay.io/grpereir/segment-backup-job:1.0.$version #my quay, can swap out with your repo
version=$(( $version + 1));

# LOCAL DEV

podman run -it --rm quay.io/grpereir/segment-backup-job:1.0.$version /bin/bash

#CHART TESTING

code $sigstore_ocp_path/charts/trusted-artifact-signer/values.yaml # replace lines 17 and possibly 16
/usr/bin/open -a "/Applications/Google Chrome.app" 'https://quay.io/repository/grpereir/segment-backup-job?tab=tags' #automated for mac but do this based on your OS
kubectl delete cronjob segment-backup-job -n sigstore-monitoring; kubectl delete job segment-backup-job -n sigstore-monitoring #if you have issues with permssions here run this as non-service account kubectl user
$segment_backup_job_repo_path/tas-easy-install.sh

```

### Testing

This job is meant to run as a service account, run this NOT in the container but logged from your client machine, this will spit out the login command that you should run on the container:

From host logged in:
```bash


export secret_name_for_sa=$( kubectl get sa segment-backup-job -n sigstore-monitoring -o json | jq ".secrets[1].name" | cut -d "\"" -f 2 )

export sa_token=$(kubectl get secret $secret_name_for_sa -n sigstore-monitoring -o json | jq .metadata.annotations."\"openshift.io/token-secret.value\"" | cut -d "\"" -f 2)
export server=$(kubectl whoami -t)
echo "kubectl login --token=$sa_token --server=$server" # spits out the login command for the SA, used in terminal 2

```

INSIDE the container:
```bash
# use the above login command, ex: kubectl login --token=... --server=...

#Choose a run type to test (installation or nightly)
export RUN_TYPE="installation" 
export RUN_TYPE="nightly"

#Verify you are the service account
kubectl whoami

#Run script as entrypoint
/opt/app-root/src/script.sh
```