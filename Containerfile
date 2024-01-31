FROM registry.redhat.io/openshift4/ose-tools-rhel8@sha256:ec47625c842cb1d042157fe32193f28fbb9ddc710eecf16c93d8fa228faa4c13 AS cli-tools
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
COPY --from=cli-tools /usr/bin/oc /usr/local/bin/oc
COPY --from=cli-tools /usr/bin/jq /usr/local/bin/jq

RUN pip install -U pip && pip install -r /opt/app-root/src/requirements.txt --force-reinstall

USER 1001