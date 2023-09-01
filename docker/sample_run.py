#!python

import os
import pathlib
import geneplexus

from google.cloud import storage


def readbucket(bucket_name, blob_name):
    """Write and read a blob from GCS using file-like IO"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Mode can be specified as wb/rb for bytes mode.
    # See: https://docs.python.org/3/library/io.html
    

    with blob.open("r") as f:
        blobdata = f.read()
        
    return(blobdata)

def writebucket(bucket_name, blob_name, data):
    """Write and read a blob from GCS using file-like IO"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Mode can be specified as wb/rb for bytes mode.
    # See: https://docs.python.org/3/library/io.html
    

    with blob.open("w") as f:
        f.write(data)
        
    return(blobdata)

datadir = os.getenv('FILE_LOC') or '.data'

job_bucket = os.getenv('GPJOBBUCKET')
job_id = os.getenv('GPJOBID')

if job_bucket and job_id:
    # attempt to read input genes
    print(f"reading input genes from cloud bucket {job_bucket}/{job_id}")
    input_genes = readbucket(bucket_name = job_bucket, blob_name = job_id)
    
else:
    print("using sample input genes for test run")
    input_genes = [
    "ARL6","BBS1","BBS10","BBS12","BBS2","BBS4","BBS5","BBS7","BBS9",
    "CCDC28B","CEP290","KIF7","MKKS","MKS1","TRIM32","TTC8","WDPCP",
    ]

    
# for net-specific docker images, this is set when the docker image is created
network = os.getenv('NETWORK') or "BioGRID" 

features = os.getenv('FEATURES') or "Embedding"
gsc = os.getenv('GSC') or "DisGeNet"


print(f"starting GP with {network} network, features = {features}, and GSC={gsc}")
myclass = geneplexus.GenePlexus(datadir, network, features, gsc )
myclass.load_genes(input_genes)

mdl_weights, df_probs, avgps = myclass.fit_and_predict()
df_sim_GO, df_sim_Dis, weights_GO, weights_Dis = myclass.make_sim_dfs()
df_edge, isolated_genes, df_edge_sym, isolated_genes_sym = myclass.make_small_edgelist(num_nodes=50)
df_convert_out_subset, positive_genes = myclass.alter_validation_df()

# mount a directory and set this env variable to save results
outdir = os.getenv('OUTDIR') or "/tmp"
print(f"saving output to {outdir}")
df_probs.to_csv(os.path.join(outdir, "df_probs.tsv"), sep="\t", header=True, index=False)
df_sim_GO.to_csv(os.path.join(outdir, "df_sim_GO.tsv"), sep="\t", header=True, index=False)
df_convert_out_subset.to_csv(os.path.join(outdir, "df_convert_out_subset.tsv"), sep="\t", header=True, index=False)


