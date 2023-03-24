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

The current docker file assumes the data is in the folder `.data` in the root of this repository and will not work if it's not in this folder. 

From the root directory (not the docker directory), issue this command

`docker build -f docker/Dockerfile -t geneplexus:latest .

This will use the data folder `.data` and build for all networks. 

To set a custom folder for the backend data, use the `DATA_FOLDER` [build argument](https://docs.docker.com/engine/reference/commandline/build/#build-arg)

`docker build --build-arg DATA_FOLDER=/path/to/data -f docker/Dockerfile -t geneplexus:latest .`

Note if you are on a new "Apple Silicon" Mac or other ARM based system, using default build will create an 'arm' 
architecture image which may not run on the cloud or other PCs.    For use on the machine on which you build this is fine.  However, 
if you want to build images for use by others or use with cloud services, you may need to build multiple 'platforms.'

This command may build those and push to docker hub (requires an account on dockerhub): 

```
DOCKERUSER=<your dockerhub user account>
docker login -u $DOCKERUSER
export NETWORK_NAME=BioGRID # set the network you want to use
docker buildx build  --platform linux/amd64,linux/arm64/v8  --build-arg NETWORK_NAME=$NETWORK_NAME -f docker/Dockerfile -t $DOCKERUSER/geneplexus:$NET --push .
```

See https://docs.docker.com/build/building/multi-platform/ for building an image that can run on both Apple CPUs and the majority of other Intel-based computers when using an Apple CPU mac.   You may need to create a new build node and then use something like this to create and push


## Optional: Net-specific dockerfile

There is an option to build a dockerfile for just one network to keep the size manageable.  
In General, 

```bash
NET=BioGRIDl; docker build --build-arg NETWORK_NAME=$NET -f docker/Dockerfile -t geneplexus:latest-$NET .
```

*NOTE: if the value of `$NET` you've assigned is not a network in the data folder, the container will still build but will not
actually including any network data and may not work (a fix is in the works)*


replace `BioGRID` above with a valid newtork name ( see )
etc.  

You would then run the container with the network of interest using the tag, e.g. 

`docker run -it geneplexus:latest-STRING python /bin/bash` (STRING network only).

etc.  

To build docker images for all networks supported by PyGenePlexus, use the following shell script.  It assumes that you have a valid python along with PyGenePlexus installed.    Note this will take a while to copy the large backend data into the docker image

```zsh
for NETWORK in `python -c "import geneplexus; print(' '.join(geneplexus.config.ALL_NETWORKS))"`
do
    buildcmd="docker build --build-arg NETWORK_NAME=$NETWORK -f docker/Dockerfile -t geneplexus:$NETWORK ."
    echo $buildcmd
done
```

See `build_net_images.sh` in the `/Docker` folder


## Testing the Containerized PyGenePlexus

Current in this early development, there is not entry point or run command.  That is forthcoming. 

You may test in two different ways by logging in with linux shell and starting python, or running the sample script. 

### example script and geneset:  

To test that PyGenePlexus with sample data, there is a test script (`sample_run.py`).  It uses environment variables as 
parameters to PyGeneplexus. 

- `$OUTDIR`
- `$FEATURES`
- `$GSC`

See the PyGeneplexus documentation for valid values for these variables. 

Note that network is set per image tag (see above).  but avaialble as an environment variable inside the container as `$NETWORK`

Data saved in the container is lost when the container exits.  To save data, you need to [connect folder on your computer to a folder in the container](https://docs.docker.com/storage/bind-mounts/).  Howeve First you need to create/designate a folder on your computer to store the output.   You'll also need to
grant Docker permission to write to this folder (in Docker Desktop, it's in settings/Resources/File Sharing).  
For example I've added the /tmp folder on my computer to settings in docker desktop, and created a folder 'gp' in tmp.   (e.g. `mkdir /tmp/gp`).   You can use any folder on your computer but must add it to file sharing in Docker settings. 


The folder inside the container can be anything, for example `/tmp/gp` In your terminal/shell, run the sample script inside docker as follows : 

```
docker run -v /tmp/gp:/tmp/gp -e OUTDIR=/tmp/gp -e FEATURES=Embedding geneplexus:BioGRID python sample_run.py
```

Then inspect the Geneplexus output files on your computer's folder /tmp/gp

To adjust the other parameters, use something similar to the following: 

```
docker run -v /tmp/gp:/tmp/gp \
    -e OUTDIR=/tmp/gp -e FEATURES=Adjacency -e GSC=GO \
    geneplexus:latest-string python sample_run.py
```


### shell: 

`docker run -it --rm geneplexus:latest-STRING`

   - replace the tag 'latest-string' with the tag for the network you want to use
   - this will start a Python console that you can `import geneplexus` and use as you.   
   - this is really valuable just for testing
   - the `--rm` option above is to delete the container after exiting, otherwise Docker will 
      keep many anonymous containers around. 
   - type `exit()` at the Python prompt to exit and delete the container (but not the image) 
   - to save outputs, you'll need to mount a folder as described above
