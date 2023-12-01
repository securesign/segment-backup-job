FROM registry.access.redhat.com/ubi9/toolbox@sha256:ac5b709f8674ee02db04cb4fc970edff1798ae974f9c0f523bd25b1b7c6bc862 AS builder

WORKDIR /tmp

RUN curl -sL https://github.com/jqlang/jq/releases/download/jq-1.6/jq-linux64 -o /tmp/jq && chmod 755 /tmp/jq && \
    curl -sL https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz -o /tmp/openshift-client-linux.tar.gz && \
    tar xvf  /tmp/openshift-client-linux.tar.gz

FROM registry.redhat.io/ubi9/python-311@sha256:944fe5d61deb208b58dbb222bbd9013231511f15ad67b193f2717ed7da8ef97b
LABEL description="This image provides a data collection service for segment"
LABEL io.k8s.description="This image provides a data collection service for segment"
LABEL io.k8s.display-name="segment collection"
LABEL io.openshift.tags="segment,segment-collection"
LABEL summary="Provides the segment data collection service"
LABEL com.redhat.component="segment-collection"


USER 0

WORKDIR /opt/app-root/src/

COPY . .
COPY --from=builder /tmp/oc /usr/local/bin/oc
COPY --from=builder /tmp/jq /usr/local/bin/jq

RUN pip install -U pip && pip install -r /opt/app-root/src/requirements.txt --force-reinstall

USER 1001