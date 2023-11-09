FROM registry.redhat.io/ubi9/python-311@sha256:dd389e922178bf32ff64c5c816bb812ab05202d6fc48ed13acc1fd1cfb6dce5e
LABEL description="This image provides a data collection service for segment"
LABEL io.k8s.description="This image provides a data collection service for segment"
LABEL io.k8s.display-name="segment collection"
LABEL io.openshift.tags="segment,segment-collection"
LABEL summary="Provides the segment data collection service"
LABEL com.redhat.component="segment-collection"

COPY . /opt/app-root/src

RUN mkdir /tmp/bin && curl https://github.com/jqlang/jq/releases/download/jq-1.6/jq-linux64 > /tmp/bin/jq && \
    chmod 755 /tmp/bin/jq && mkdir /tmp/oc && \
    curl -L https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz > /tmp/oc/openshift-client-linux.tar.gz && cd /tmp/oc && \
    tar xvf openshift-client-linux.tar.gz && export PATH=$PATH:/tmp/oc && \
    python3 -m pip install analytics
