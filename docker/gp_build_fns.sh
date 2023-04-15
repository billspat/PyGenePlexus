# gp_build_fns.sh 
# functions to initiate building, pushing and running GP jobs on GCP. 
# requirements: 
#  - Docker buildkit (aka buildx) installed: https://docs.docker.com/build/install-buildx/
#  - data in the .data directory
#  - Google cloud cli installed
#  - google cloud logged in and project set with billing to run jobs
#  - google cloud container registry created in project
#
# Usage:
# in terminal source this script, possibly from root of project : source docker/building_gp.sh
# run functions with the network name as a parameter.  Network name must match case used in GP. 
# to see network names, use echo $GP_NETWORKS
# example  
# gp_build STRING
# gp_push STRING
# gp_run STRING

# TO DO - allow parameters from this script.  see code in gp_run for how to set params
# 

# array of networks as of spring 23 that GP uses
export GP_NETWORKS=("BioGRID" "STRING" "STRING-EXP" "GIANT-TN")
# can get this list using python, importing gp and printing this list

gp_build() {
    # builds network specific docker image that works in cloud (e.g. x86)
    # uses docker buildkit so that we can build using Apple Silicon

    # run this from the root dir of the project
    if [ $# -lt 1 ]
    then
        echo "You must include the Network name. Usage: $funcstack[1] GPNETWORKNAME"
        return 1
    fi
    NETWORK_NAME=$1
    if (($GP_NETWORKS[(Ie)$NETWORK_NAME])); then
        echo "building image geneplexus:$NETWORK_NAME for linux/amd64"
        docker buildx build  --platform linux/amd64  \
        --build-arg NETWORK_NAME=$NETWORK_NAME \
        -f docker/Dockerfile -t geneplexus:$NETWORK_NAME --load .
    else
        echo "Network must be one of $GP_NETWORKS, you sent $NETWORK_NAME"
    fi
}

# after building local, push to GCP

gp_gcp_push() {
    # this pushes the gp image up to google cloud, but 
    # requires significant work to setup local authentication
    # https://cloud.google.com/container-registry/docs/pushing-and-pulling
    # https://cloud.google.com/container-registry/docs/advanced-authentication

    if [ $# -lt 1 ]
    then
        echo "You must include the Network name. Usage: $funcstack[1] GPNETWORKNAME"
        return 1
    fi
    
    NETWORK_NAME=$1

    export GCP_PROJECT=$(gcloud config get-value project)
    export GCP_IMAGENAME=gcr.io/$GCP_PROJECT/geneplexus:$NETWORK_NAME

    docker tag geneplexus:$NETWORK_NAME $GCP_IMAGENAME
    ### lots of authentication stuff I don't remember
    docker push $GCP_IMAGENAME

    # wait for it...
}

# alternative: build cloud
# this doesn't work for images that include the network becuase 
# 1  excludes everything in gitignore AND dockerignore, 
#    so to requires editing .gitignore to be able to include the .data folder
# 2. creates tarball of whole folder including .data wichi is 32gb, and 
#    and that alone takes a long time
# options to try it : 
# 1.  first comment out the .data line in .gitignore
# 2. run one of
#    gcloud builds submit -t "$GCP_IMAGENAME"
#    OR
#    gcloud builds submit --config cloudbuild.yaml .
#    # this last command requires cloudbild.yaml file which may not be pushed


###### running

gp_gcp_run() {
    # DRAFT create job name based on network, must be lower case
    # this shows how to create and execute a job on GCP
    # issues
    # a. uses the default params and just runs the sample_run.py code
    # b. assumes the name of image follows same template as the build script above
    # c. assumes you have google cloud cli installed and you are logged in
    if [ $# -lt 1 ]
    then
        echo "You must include the Network name. for example: gp_gcp_run BioGRID"
        return 1
    fi
    
    NETWORK_NAME=$1

    GCP_IMAGENAME=gcr.io/$GCP_PROJECT/geneplexus:$NETWORK_NAME
    GCP_JOBNAME=gp$( echo $NETWORK_NAME | tr '[:upper:]' '[:lower:]')


    # https://cloud.google.com/run/docs/managing/jobs#command-line_1
    # https://cloud.google.com/sdk/gcloud/reference/run/jobs/create

    # this can handle string but probably not GIANT without upping the cpu and memory
    # for CPU/MEM settings, see https://cloud.google.com/run/docs/configuring/memory-limits#command-line
    # TODO set cpu and memory depending on network
    # TODO send actual parameters and genelist
    GCLOUD_REGION=us-west2
    gcloud run jobs create $GCP_JOBNAME \
        --image $GCP_IMAGENAME \
        --tasks 1 \
        --set-env-vars FEATURES=Adjacency \
        --set-env-vars GSC=GO \
        --max-retries 0 \
        --region $GCLOUD_REGION \
        --execute-now \
        --cpu 4 \
        --memory 8G \
        --task-timeout=1200 \
        --command sample_run.py 
        # --labels=created_by=$USER

        gcloud run jobs list --region $GCLOUD_REGION
        gcloud run jobs describe --region $GCLOUD_REGION $GCP_JOBNAME
}