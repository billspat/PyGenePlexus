## Using Docker with GenePlexus

This folder is for building a docker container to run Geneplexus.  


## Getting the Data

The design decision is to include the support data ('backend' data) inside the docker container to make it easier to run and share. 

the gp package has facility for downloading the backend data when you run it automatically.   However the Docker image needs 
all of the data so we provide a script for doing that.   This requires the gp package to te installed.  

*NOTE:* This will attempt to download the data needed for all combinations of GP parameters which is approximately 15 gb.   Downloading
this much data from Zenodo may prove problematic as it may take 10-30 minutes and may not finish.  

### Installing prior to initiating download

1. create a virtual env if you haven't already.  Ther eare many ways to do this, this example uses virtualenv, and assumes you have 
both python and virtualenv installed ( https://virtualenv.pypa.io/en/latest/ )

```
# in the PyGenePlexus folder
virtualenv -p=3.10 .venv
source .venv/bin/activate
# upgrade pip to the latest
pip install --upgrade pip
# install this package and all the package it needs
pip install --editable .
```

### Initiating download

Now you can run the script to download data into a `.data` folder inside this package. 

```
python docker/download_for_docker.py
```
Which will download data for all networks and features into the `./data` folder.    

Optionally you can specify a different folder and list of networks (if for example the download is interrupted half way).  
For details run the command with the help option

```
python docker/download_for_docker.py -h
```


## Managing disk space available to Docker

Note that building this container requires approximately 30 gb of free disk space, and 15gb of disk space available to Docker just for 
this image and additional storage for any other images you create.  Unless you change the maximum size of the container (default 10gb) you 
may get the error message "no space left on device"

On MacOS you must change this limit in docker desktop settings, resourdces section, increase the 'virtual disk limit'.    It's unclear (and not well documented) how to do this on Windows or Linux.  
cloud services have their own limits for image sizes.   For information on tis for the docker cli, see https://docs.docker.com/engine/reference/commandline/dockerd/#storage-driver-options related to the option `dm.basesize`

In addition you may hit the disk size limit becuase of previous images and containers.  You can remove any old images with `docker system prune`

If you are sure you can remove all images, layers and containers not currently being used, you can use 

`docker system prune --all` 

which may free up enough space. 

## Building Dockerfile

This assumes the data has already been downloaded onto your computer and that Docker (or Docker desktop) is installed. 

The current docker file assumes the data is in the folder `.data` in the root of this repository and will not work if it's not
in this folder. 

From the root directory (not the docker directory), issue this command

`docker build -f docker/Dockerfile -t geneplexus:latest .

## Testing the Containerized PyGenePlexus

Current in this early development, there is not entry point or run command.  That is forthcoming. 

However, to test that PyGenePlexus and the data are working in the docker image, you can do the following: 

In your terminal/shell, connect to the image with a bash shell : 

```
docker run -it geneplexus:latest /bin/bash
# (base) root@3ceef97aee0f:/#
```

Once in the container, start python: `(base) root@3ceef97aee0f:/# python`

```
Python 3.10.8 (main, Nov 24 2022, 14:06:33) [GCC 11.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

try running an example program inside python

```python
import os
import pathlib
import geneplexus

input_genes = [
    "ARL6","BBS1","BBS10","BBS12","BBS2","BBS4","BBS5","BBS7","BBS9",
    "CCDC28B","CEP290","KIF7","MKKS","MKS1","TRIM32","TTC8","WDPCP",
]

datadir = "/PyGenePlexus/.data"
outdir = "/tmp"

myclass = geneplexus.GenePlexus(datadir, "STRING", "Embedding", "DisGeNet")
myclass.load_genes(input_genes)

mdl_weights, df_probs, avgps = myclass.fit_and_predict()
df_sim_GO, df_sim_Dis, weights_GO, weights_Dis = myclass.make_sim_dfs()
df_edge, isolated_genes, df_edge_sym, isolated_genes_sym = myclass.make_small_edgelist(num_nodes=50)
df_convert_out_subset, positive_genes = myclass.alter_validation_df()
# save 
df_probs.to_csv(osp.join(outdir, "df_probs.tsv"), sep="\t", header=True, index=False)
df_sim_GO.to_csv(osp.join(outdir, "df_sim_GO.tsv"), sep="\t", header=True, index=False)
df_convert_out_subset.to_csv(osp.join(outdir, "df_convert_out_subset.tsv"), sep="\t", header=True, index=False)
exit()
```

then check the contents of the files in the `\tmp` folder.  



