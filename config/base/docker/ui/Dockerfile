FROM ubuntu:16.04

# Install NodeJS
RUN apt-get update && \
    apt-get install -y git curl python3-software-properties && \
    curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get install -y nodejs

# Clone UI repository
RUN cd /home && \
    git clone https://github.com/mlrepa/mlpanel-ui.git && \
    cd mlpanel-ui && \
    npm install

WORKDIR /home/mlpanel-ui

CMD git pull origin master && export REACT_APP_API_URL=http://${HOST_IP}:8089/ && npm start
