#!python

import os
import pathlib
import geneplexus

input_genes = [
    "ARL6","BBS1","BBS10","BBS12","BBS2","BBS4","BBS5","BBS7","BBS9",
    "CCDC28B","CEP290","KIF7","MKKS","MKS1","TRIM32","TTC8","WDPCP",
]

datadir = os.getenv('FILE_LOC') or '.data'

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
