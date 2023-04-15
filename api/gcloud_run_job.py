# gcloud_run_job.py

# functions to create and execute google cloud run job 
# this is only a demo and has several hard-coded values for now
# uses a container created with google cloud run job quickstart
# requires 
# pip install google-cloud-run
# set project_id in env first with  export GOOGLE_CLOUD_PROJECT=<my project_id>

# limitations: this does not set number of CPU or memory for job execution.  Don't know where to set those
# so probably can only run BioGRID networks for now

import os, json, requests
from google.cloud import run_v2
from google.protobuf.duration_pb2 import Duration


def create_container(project_id, image_name,env_vars={}):
    """ create container object for job to run, including particulars for env vars and cmd """
    # container is where you set command options and env variables
    # https://cloud.google.com/python/docs/reference/run/latest/google.cloud.run_v2.types.Container

    # this uses the soon-to-be 
    image_url = f"gcr.io/{project_id}/{image_name}"
    container_name = f"{image_name}-container"

    # convert dict into MutableSequence[google.cloud.run_v2.types.EnvVar] for container
    job_env = []
    for name in env_vars: 
        print(name, env_vars[name])
        ev = run_v2.EnvVar({'name':name, 'value':str(env_vars[name])})
        job_env.append(ev)

    job_container = run_v2.Container(
        {'name':container_name, 
         'image' : image_url,
         'env' : job_env
         })
    
    return(job_container)


def create_job(project_id, location, job_id, job_container, job_timeout=1200):
    """create and execute a job"""

    client = run_v2.JobsClient()
    job = run_v2.Job()
    
    from google.protobuf.duration_pb2 import Duration
    
    timeout_duration = Duration()
    timeout_duration.FromSeconds(job_timeout)
    
    # job.tempate.template: https://cloud.google.com/python/docs/reference/run/latest/google.cloud.run_v2.types.TaskTemplate
    task_template = run_v2.TaskTemplate({
        'containers' : [job_container],
        'max_retries' : 1,
        'timeout' : timeout_duration
        } )
    # TODO: be explicit about type of VM, if possible?  'execution_environment' # https://cloud.google.com/python/docs/reference/run/latest/google.cloud.run_v2.types.ExecutionEnvironment

    # job.template : https://cloud.google.com/python/docs/reference/run/latest/google.cloud.run_v2.types.ExecutionTemplate    
    job.template = run_v2.ExecutionTemplate({
        'task_count' : 1,
        'template' : task_template
    })

    print(f"creating {job_id}")
    
    creation_request = run_v2.CreateJobRequest(
            parent=f"projects/{project_id}/locations/{location}",
            job=job,
            job_id=job_id,
        )

    # Make the request
    operation = client.create_job(request=creation_request)
    response = operation.result()
    return(response)


def run_job(project_id, location, job_id ):
    """ creating a job does not run it, have to create an execution"""
    
    client = run_v2.JobsClient()

    # TODO: check if job is actually ready?   use run_v2 client get job(job_id)  if job_response.terminal_condition.type_ =='Ready':

    job_full_name = f"projects/{project_id}/locations/{location}/jobs/{job_id}"
    
    # reference https://cloud.google.com/python/docs/reference/run/latest/google.cloud.run_v2.types.RunJobRequest
    run_request = run_v2.RunJobRequest(
        name=job_full_name,  # the full name of the job
        )
    # Make the request
    run_operation = client.run_job(request=run_request)
    # this could take a very long time here, is there an async client or method?
    run_response = run_operation.result()
    
    return(run_response)


def run_geneplexus_job(gp_network="BioGRID", location="us-west2"):
    """ hard-coded specific test of the Geneplexus image.  This would be moved into
    the api server to kick off the job"""
    project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise RuntimeError(' GCP project could not be found in environment')
    
    
    # currently gp images are named this with, with network as tag
    image_name = f"geneplexus:{gp_network}"

    import random, string
    randstr = ''.join(random.choices(string.ascii_lowercase, k=5))
    job_id = f"gp-{gp_network}-{randstr}"
    
    env_vars = {
        'FEATURES': "Embedding",
        'GSC': "DisGeNet"
    
    }

    job_container = create_container(project_id, image_name, env_vars)
    print(f"creating {job_id}")
    job_response = create_job(project_id, location, job_id, job_container)
    print(job_response)
    if job_response.terminal_condition.type_ =='Ready':
        run_response = run_job(project_id, location, job_id)
        print(run_response)
    else: 
        print("job {job_id} does not say ready")


