FROM python:3.7

RUN pip install email-validator==1.0.5 \
                fastapi==0.42.0 \
                google-api-python-client==1.7.9 \
                google-cloud-storage==1.20.0 \
                jinja2==2.10.3 \
                mlflow==1.4.0 \
                oauth2client==3.0.0 \
                psutil==5.6.2 \
                python-multipart==0.0.5 \
                pytest==5.2.2 \
                pyyaml==5.1.2 \
                requests==2.22.0 \
                scikit-learn==0.20.4 \
                uvicorn==0.10.8

RUN apt-get update && \
    apt-get install -y sudo && \
    useradd -m user -u 1000 && \
    echo 'user:user' | chpasswd user && \
    echo "user ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/user && \
    chmod 0440 /etc/sudoers.d/user && \
    chown -R user /home


RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz

# Installing the package
RUN mkdir -p /usr/local/gcloud \
  && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
  && /usr/local/gcloud/google-cloud-sdk/install.sh

# Adding the package path to local
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

USER user

WORKDIR /home/deploy

ENV PYTHONPATH=/home

CMD sudo chown -R user $WORKSPACE && uvicorn --host 0.0.0.0 --port 9000 src.app:app --reload
