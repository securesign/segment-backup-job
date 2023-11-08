FROM registry.redhat.io/rhel9/python-311
RUN mkdir /tmp/bin

RUN curl https://github.com/jqlang/jq/releases/download/jq-1.6/jq-linux64 > /tmp/bin/jq
RUN chmod 755 /tmp/bin/jq

RUN mkdir /tmp/oc
RUN curl -L https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz > /tmp/oc/openshift-client-linux.tar.gz
RUN tar xvf /tmp/oc/openshift-client-linux.tar.gz
RUN cd /tmp/oc/
RUN mv oc /tmp/bin/oc

COPY . /opt/app-root/src
RUN export PATH=$PATH:/tmp/bin/
RUN  python3 -m pip install analytics
