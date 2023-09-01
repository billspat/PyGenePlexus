#!bash

for NET in `python -c "import geneplexus; print(' '.join(geneplexus.config.ALL_NETWORKS))"`
do
    buildcmd="docker build --build-arg NETWORK_NAME=$NET -f docker/Dockerfile -t geneplexus:$NET ."
    echo $buildcmd
    $(buildcmd)
done