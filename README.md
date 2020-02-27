# mlpanel

GitBook docs: https://mlrepa.gitbook.io/mlpanel/

## Preparations

### Create *config/.env*

* **if you are going to use GCS bucket as artifact storage**, put into *config/* Google credentials json
 
* create file *config/.env*:
```.env

# Common
HOST_MODE=[local|remote]
WORKSPACE=/path/to/workspace/folder/on/host
GOOGLE_APPLICATION_CREDENTIALS=/home/config/<credentials.json>

# Deploy
GCP_PROJECT=vision-230607
GCP_ZONE=us-east1-b
GCP_MACHINE_TYPE=g1-small
GCP_OS_IMAGE=ubuntu1804-docker
GCP_BUCKET=<bucket>
MODEL_DEPLOY_DOCKER_IMAGE=meisterurian/mlflow-deploy
MODEL_DEPLOY_DEFAULT_PORT=5000
MODEL_DEPLOY_FIREWALL_RULE=mlflow-deploy

# Projects
LOGLEVEL=<DEBUG|INFO|WARNING|WARN|ERROR|FATAL|CRITICAL>
ARTIFACT_STORE=[mlruns|gs://<bucket>]
MLFLOW_TRACKING_SERVERS_PORTS_RANGE=5000-5020

# UI
MLPANEL_UI_BRANCH=feature/ui-features
REACT_APP_API_URL=http://0.0.0.0:8080/
```


### Description of environment variables

#### Common

#####  ***HOST_MODE***

Required: No.

Default: local.

Defines ip address of tracking servers: 

* if *local* then ip address = "0.0.0.0" (e.i. **mlpanel** is running and available locally);
* if *remote* then ip address = <external_ip> (e.i. **mlpanel** is running on some remote server and available by external ip);
external ip is detected automatically.


##### ***WORKSPACE***

Required: Yes.

WORKSPACE sets path to workspace folder - any path on you disk (taking into account permission).

The folder contains:

* projects database;
* deploy database;
* folders for each project, each folder is named by the project id and contains:
    * mlflow.db - mlflow database;
    * artifact storage folder - if variable *ARTIFACT_STORE* points to local path.
    
**Note**: if artifacts are stored locally then folder WORKSPACE can have huge size, it depends on 
number of projects and artifacts (especially ML models) volume.


##### ***GOOGLE_APPLICATION_CREDENTIALS***

Required: No.

Defines path to your Google credentials JSON (https://cloud.google.com/docs/authentication/getting-started) 
inside docker container.

Consists from two parts: fixed (/home/config/ - exact path of folder config inside container) and name of your JSON.  
The JSON you must put to folder config/.

**Note** define *GOOGLE_APPLICATION_CREDENTIALS* if you are going to use Google Cloud Storage 
(https://cloud.google.com/storage) or/and deploy models on Google Compute Engine (GCE, https://cloud.google.com/compute).


#### Deploy

Now two types of deployments exist:

* local - deploys model locally (as new MLflow model server process inside container);
* gcp - start new GCE instance and run MLflow model server process on it.

##### ***GCP_PROJECT***

Required: No (Yes for deploying on GCE).

Id of your project Google Cloud Platform. Define it if you are going to deploy models on GCE.


##### ***GCP_ZONE***

Required: No (Yes for deploying on GCE).

Zone type for instances. More about zone: https://cloud.google.com/compute/docs/regions-zones.

##### ***GCP_MACHINE_TYPE***

Required: No (Yes for deploying on GCE).

GCE machine type. More about machine types: https://cloud.google.com/compute/docs/machine-types.

Minimum requirement of machine type is *g1-small*.

##### ***GCP_OS_IMAGE***

Required: No (Yes for deploying on GCE).

Your private (custom) OS image. Docker must be installed inside OS image. 
Working with OS images: https://cloud.google.com/compute/docs/images/create-delete-deprecate-private-images.


##### ***GCP_BUCKET***

Required: No (Yes for deploying on GCE).

Google Storage bucket name.


##### ***MODEL_DEPLOY_DOCKER_IMAGE***

Required: No (Yes for deploying on GCE).

Name of docker image which provides running of deployment container on GCE instance. 
MLflow must be installed in the image.


##### ***MODEL_DEPLOY_DEFAULT_PORT*** 

Required: No (Yes for deploying on GCE).

Port on which deployments are available.

**Note**: all gcp deployment have the same port, but theirs external ip addresses are different.


##### ***MODEL_DEPLOY_FIREWALL_RULE***

Required: No (Yes for deploying on GCE).

Name of firewall rule. Firewall rule is required to open some port(s) for communication with services running on 
GCE instances. More about firewall: https://cloud.google.com/vpc/docs/using-firewalls.


#### Projects

##### ***LOGLEVEL***

Required: No.

Default: INFO.

Logging level in service *projects*.


##### ***ARTIFACT_STORE***

Required: Yes.

Path to artifact store. It can be:

* name of folder - it means relative path in $WORKSPACE/<project_folder>, e.g.:
```
ARTIFACT_STORE=mlruns => full path of artifact store is $WORKSPACE/<project_folder>/mlruns.
```

* Google Storage bucket in format **gs://<bucket_name>**; this case requires to 
define variable *GOOGLE_APPLICATION_CREDENTIALS*.


##### ***MLFLOW_TRACKING_SERVERS_PORTS_RANGE***

Required: Yes.

Format: <start_port>-<end_port>.

Range of ports for tracking servers. It also defines how many projects can be 
created: one port corresponds to one project (tracking server).


#### UI

##### ***MLPANEL_UI_BRANCH***

Required: Yes.

[mlpanel-ui](https://github.com/mlrepa/mlpanel-ui) branch. 
It can be any existing branch name.


##### ***REACT_APP_API_URL***

Required: Yes.
Fixed value: http://0.0.0.0:8080/.

URL to API which UI service calls.


## Build

```bash
ln -sf config/.env && docker-compose build
```

## Run services

```bash
docker-compose up
```

### Enter UI

`http://<host>:3000`,
where `host` = *localhost* or *remote server ip*


## Tests and examples

Read **README.md** files in *services/*:

* [projects](services/projects/README.md);  
* [deploy](services/deploy/README.md).
