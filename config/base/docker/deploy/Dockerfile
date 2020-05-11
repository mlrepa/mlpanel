FROM mlrepa/mlpanel-base:latest

# Google Cloud SDK installation
RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz \
  && mkdir -p /home/user/gcloud \
  && tar -C /home/user/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
  && /home/user/gcloud/google-cloud-sdk/install.sh -q
# Adding the package path to local
ENV PATH $PATH:/home/user/gcloud/google-cloud-sdk/bin


COPY ./requirements.txt /tmp/requirements.txt
RUN sudo pip install -r /tmp/requirements.txt

WORKDIR /home/deploy

CMD chmod +x startup.sh && ./startup.sh
