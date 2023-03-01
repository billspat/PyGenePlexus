FROM continuumio/miniconda3:latest

# assumes all data needed is downloaded to the .data folder in this repo

# RUN mkdir PyGenePlexus

# copy all code and data
COPY . PyGenePlexus
# COPY geneplexus PyGenePlexus/geneplexus
# COPY pyproject.toml PyGenePlexus
# COPY setup.cfg PyGenePlexus
# COPY setup.py PyGenePlexus
# COPY tox.in PyGenePlexus
# COPY MANIFEST.in PyGenePlexus
# COPY test PyGenePlexus
# COPY .data .data
# COPY example example

# RUN mkdir -p ~/.data/geneplexus && \
RUN pip install ./PyGenePlexus && pip install -r PyGenePlexus/requirements-dev.txt

ENV FILE_LOC=/PyGenePlexus/.data

# COPY download_for_docker.sh .
# RUN chmod u+x ./download_for_docker.sh && /bin/sh -c ./download_for_docker.sh


