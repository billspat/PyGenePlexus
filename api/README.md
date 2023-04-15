### Geneplexus API

this wraps a basic api using the fastapi framework around the main gp data pipeline

## prep

Install geneplexus from this package or from pip

```
cd api # this directory
pip install -r requirements.txt
```

data must be present in a known location

## to run the api server

1. cd to this directory (currently a subdir of main dir)
1. `export FILE_LOC=../.data; export NETWORK=BioGRID; uvicorn  --host 0.0.0.0 --port 8000 --app-dir /geneplexus/api gpapi:app --reload`
1. visit http://localhost:8000/docs to see api documentation provided by fastapi

Note that using the fastapi auto-doc (e.g. swagger) to run a test pipeline on 'run' test execution will complete but 
won't show the output as it's too large (3.5M)

## running Geneplexus via the api

See documentation via local server to see the contruction of input, but that must be part of the request body.  There are no 'parameters' 
( e.g. no options in the URL, only in the request body which must also contain the gene list (geneset ))

## testing 

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

