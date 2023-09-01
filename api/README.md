### Geneplexus API

this wraps a basic api using the fastapi framework around the main gp data pipeline

## prep

Install geneplexus from this package or from pip

```
cd api # this directory
pip install -r requirements.txt
```

data must be present in a known location

## to run the api server locally

1. cd to this directory (currently a subdir of main dir)
1. `export FILE_LOC=../.data; export NETWORK=BioGRID; uvicorn  --host 0.0.0.0 --port 8000  gpapi:app --reload`
1. visit http://localhost:8000/docs to see api documentation provided by fastapi

Note that using the fastapi auto-doc (e.g. swagger) to run a test pipeline on 'run' test execution will complete but 
won't show the output as it's too large (3.5M)

## running Geneplexus via the api

See documentation via local server to see the contruction of input, but that must be part of the request body.  There are no 'parameters' 
( e.g. no options in the URL, only in the request body which must also contain the gene list (geneset ))

### testing 

From the command line, use the curl utility to  construct a request

```
curl -X 'POST' \
  'http://127.0.0.1:8000/run/' -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "net_type": "BioGRID", "features": "Embedding",   "gsc": "GO",   "geneset": [
    "ARL6","BBS1","BBS10","BBS12","BBS2","BBS4","BBS5","BBS7","BBS9","CCDC28B","CEP290","KIF7","MKKS","MKS1","TRIM32","TTC8","WDPCP"
  ]
}' > /tmp/testgpoutput.json
```

*this output json is quite large and it does not contain any line-breaks, so it's recommened to use the `less` utility 
on the command line, or code editor to examine the output, eg. 

`less /tmp/testgpoutput.json`

## Containerized API

The `/api` folder containers a  `Dockerfile` to create an image to run the API but does have any data.  It also includes a `cloudbuild.yaml` file used to build the container 
order to create a container for the API to 


## Cloud IAM

The goal is to incorporate functions to create the resources needed and then run the GP models in the cloud.  
the system must have the container(s) built and pushed to the cloud repository to use for running these models. 
See the `/docker` folder for more information about that. 


**API Server**

For the API server to be able to create and use cloud resources the service account in which it runs must have access to a storage account. 

API Server will run under a service account, and that account must be given permission to 

 - run a cloud run service
     - may include accessing network service
 - read & write from cloud storage
 - run & exec cloud run jobs
     - https://cloud.google.com/run/docs/create-jobs
     - may require read access to container registry

The job that is created must run under a service account.  
could we use the same account as above 
In addition the API server and the model runner exchange inputs and outputs using cloud storage rather than http.   

```
SERVICE_ACCOUNT_NAME=X
CRED_FILE_NAME=credfile.json
gcloud iam service-accounts keys create $CRED_FILE_NAME --iam-account $SERVICE_ACCOUNT_NAME
# 
```

references: 

https://cloud.google.com/run/docs/securing/service-identity


**Container/Job**

The container only needs access to storage.    