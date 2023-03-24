FROM python:3.10-bullseye
# FROM continuumio/miniconda3:latest

# assumes all data needed is downloaded to the .data folder in this repo

# RUN mkdir PyGenePlexus
ARG NETWORK_NAME=*
ENV NETWORK=${NETWORK_NAME}
#ALL_NETWORKS = ["BioGRID", "STRING", "STRING-EXP", "GIANT-TN"]


# copy code needed, and install local package
# COPY . PyGenePlexus
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
ENV FILE_LOC=${APPDIR}/.data
WORKDIR ${APPDIR}
COPY api api

# COPY api/requirements.txt api-requirements.txt
RUN pip install -r api/requirements.txt && pip install ${code_dir} 
# && pip install -r ${code_dir}/requirements-dev.txt

# this copies just the data files for the network ARG
# if none sent, use the * glob character which should copy all of them
RUN mkdir $FILE_LOC
COPY .data/*_${NETWORK_NAME}_* $FILE_LOC
COPY .data/*_${NETWORK_NAME}.txt $FILE_LOC
COPY .data/*_${NETWORK_NAME}.npy $FILE_LOC
COPY .data/*_${NETWORK_NAME}.edg $FILE_LOC
COPY .data/IDconversion* $FILE_LOC
COPY .data/GSCOriginal_* $FILE_LOC

COPY .data/NodeOrder_* $FILE_LOC
COPY example example
COPY docker/sample_run.py .
EXPOSE 8000
ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "api", "gpapi:app"]