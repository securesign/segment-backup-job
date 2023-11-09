FROM registry.redhat.io/rhel9/python-311@sha256:1e0e60ebb9ba064e040f6668380b7caa830def2b3ea9df17d954fdafe280f2c0
LABEL description="This image provides a data collection service for segment"
LABEL io.k8s.description="This image provides a data collection service for segment"
LABEL io.k8s.display-name="segment collection"
LABEL io.openshift.tags="segment,segment-collection"
LABEL summary="Provides the segment data collection service"
LABEL com.redhat.component="segment-collection"
LABEL name="segment-collection"

COPY . /opt/app-root/src

RUN mkdir /tmp/bin && curl https://github.com/jqlang/jq/releases/download/jq-1.6/jq-linux64 > /tmp/bin/jq && \
    chmod 755 /tmp/bin/jq && mkdir /tmp/oc && \
    curl -L https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz > /tmp/oc/openshift-client-linux.tar.gz && cd /tmp/oc && \
    tar xvf openshift-client-linux.tar.gz && export PATH=$PATH:/tmp/oc && \
    python3 -m pip install analytics
