FROM cccs/assemblyline-v4-service-base:stable

ENV SERVICE_PATH msg_parser.MsgParser

USER root

RUN apt update
RUN pip3 install extract-msg natsort

USER assemblyline

WORKDIR /opt/al_service
COPY . .

ARG version=4.0.0.dev1
USER root
RUN sed -i -e "s/\$SERVICE_TAG/$version/g" service_manifest.yml

USER assemblyline
