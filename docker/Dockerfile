FROM python:3.10-bullseye

# PyGenePlexus Dockerfile
# container to run PyGeneplexus for specific network from command line

# Configuration for Cloud environment
# will flush print buffers immediately, good if system crashes
# see https://stackoverflow.com/questions/60828641/simplest-way-to-perform-logging-from-google-cloud-RUN
ENV PYTHONUNBUFFERED True

# docker build arguments - set these at build time
# the location of the GP backend data on this computer to be copied into this container
# default assumes a subfolder of current dir named .data 
ARG DATA_FOLDER=.data
# the name of GP gene network matching the case of the files (eg. 'BioGRID')
# the default '*' is all networks and _may_ work but may have issues at run time
ARG NETWORK_NAME=*
ENV NETWORK=${NETWORK_NAME}
#ALL_NETWORKS = ["BioGRID", "STRING", "STRING-EXP", "GIANT-TN"]


# copy code needed, and install local package
# COPY . PyGenePlexus # previous command
ENV code_dir=/tmp/PyGenePlexus
RUN mkdir -p ${code_dir}
COPY geneplexus ${code_dir}/geneplexus
COPY pyproject.toml ${code_dir}
COPY setup.cfg ${code_dir}
COPY setup.py ${code_dir}
COPY tox.ini ${code_dir}
COPY MANIFEST.in ${code_dir}
COPY test ${code_dir}
COPY requirements-dev.txt ${code_dir}


# create a working folder and copy useable code in there
ENV APPDIR=/geneplexus
# FILE_LOC is used in places in the PyGenePlexus codebase to indicate data folder 
ENV FILE_LOC=${APPDIR}/.data
WORKDIR ${APPDIR}

# note, this image does not use the API, only runs PyGP 

# note, this image does not use the API, only runs PyGP 
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt &&  pip install ${code_dir} \
    && pip install -r ${code_dir}/requirements-dev.txt

# this copies just the data files for the network ARG
# if none sent, use the * glob character which should copy all of them
RUN mkdir $FILE_LOC
COPY ${DATA_FOLDER}/*_${NETWORK_NAME}_* $FILE_LOC
COPY ${DATA_FOLDER}/*_${NETWORK_NAME}.txt $FILE_LOC
COPY ${DATA_FOLDER}/*_${NETWORK_NAME}.npy $FILE_LOC
COPY ${DATA_FOLDER}/*_${NETWORK_NAME}.edg $FILE_LOC
COPY ${DATA_FOLDER}/IDconversion* $FILE_LOC
COPY ${DATA_FOLDER}/GSCOriginal_* $FILE_LOC
COPY ${DATA_FOLDER}/NodeOrder_* $FILE_LOC

COPY example example
COPY docker/sample_run.py .
COPY docker/run_gp.py .
ENTRYPOINT ["python"]
CMD ["sample_run.py"]