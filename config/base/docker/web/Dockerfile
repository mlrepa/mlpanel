FROM ubuntu:16.04

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:nginx/stable && \
    apt-get update && \
    apt-get install -y nginx-extras && \
    rm -rf /var/cache/apt && rm -rf /var/lib/apt


CMD nginx -g 'daemon off;'