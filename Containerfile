FROM registry.redhat.io/ubi9/python-311@sha256:944fe5d61deb208b58dbb222bbd9013231511f15ad67b193f2717ed7da8ef97b
LABEL description="This image provides a data collection service for segment"
LABEL io.k8s.description="This image provides a data collection service for segment"
LABEL io.k8s.display-name="segment collection"
LABEL io.openshift.tags="segment,segment-collection"
LABEL summary="Provides the segment data collection service"
LABEL com.redhat.component="segment-collection"

COPY . /opt/app-root/src

USER 0

RUN mkdir /opt/app-root/src/bin && cd /opt/app-root/src/bin && \
    curl -sLO https://github.com/jqlang/jq/releases/download/jq-1.6/jq-linux64 && \
    mv jq-linux64 jq && chmod 755 /opt/app-root/src/bin/jq && mkdir /tmp/oc && \
    curl -L https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz > /tmp/oc/openshift-client-linux.tar.gz && cd /tmp/oc && \
    tar xvf openshift-client-linux.tar.gz && mv /tmp/oc/oc /opt/app-root/src/bin/oc && \
    cd /opt/app-root/src/ && export PATH=$PATH:/opt/app-root/src/bin && \
    /opt/app-root/bin/pip install --upgrade pip && /opt/app-root/bin/pip install -r /opt/app-root/src/requirements.txt --force-reinstall

USER 1001