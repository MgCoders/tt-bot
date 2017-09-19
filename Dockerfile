#!/usr/bin/env bash

FROM dataquestio/python2-starter

# Export env settings
ENV TERM=xterm
ENV LANG en_US.UTF-8

ADD /requirements/ /tmp/requirements
RUN /opt/ds/bin/pip install -r /tmp/requirements/post-requirements.txt

ADD /bot/ /home/ds/notebooks
