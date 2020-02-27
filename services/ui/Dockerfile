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
    git checkout $MLPANEL_UI_BRANCH

WORKDIR /home/mlpanel-ui

RUN npm install

# At each run check updates
CMD git fetch && git checkout $MLPANEL_UI_BRANCH && git pull origin $MLPANEL_UI_BRANCH && npm start
