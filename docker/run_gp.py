"""
run_geneplexus : method to run the geneplexus pipeline from the command line givnen 

usage : 
"""
import logging
import os, sys, json

from geneplexus import geneplexus

def run_and_save(job_name, results_store, data_path, logging, 
    net_type=None,
    features=None,
    GSC=None
    ):
    
    """ gather parameters and check that everything is in place to run the model.  Log errors and status"""

    logging.info("reading input_genes_file ")
    try:
        gene_list = results_store.read_input_file(job_name)
        if gene_list:
            gene_count = str(len(gene_list))
            logging.info(f"read {gene_count} genes")
            logging.info(str(gene_list))
        else:
            logging.error(f"job {job_name} no data in input file")

    except Exception as e:
        err_msg = "reading input file error: " + str(e)
        logging.error(err_msg)
        raise


    # set default parameters
    net_type = net_type or 'BioGRID'
    features = features or 'Embedding'
    GSC = GSC or 'GO'

    try:   
        logging.info('starting gp model run')
        results_store.save_status(job_name, "started")
        df_probs, df_GO, df_dis, avgps, df_edgelist, df_convert_out, positive_genes = run_model(data_path, gene_list, net_type, features, GSC)
        graph = make_graph(df_edgelist, df_probs)

        logging.info('gp model complete')

    except Exception as e:
        err_msg = "run_model error: " + str(e)
        logging.error(err_msg)
        results_store.save_status(job_name, "failed")
        raise

    try:
        input_count = df_convert_out.shape[0]
    except Exception as e:
        err_msg = "df_convert_out error: " + str(e)
        logging.error(err_msg)
        results_store.save_status(job_name, "failed")
        raise

    try:
        results_store.save_status(job_name, "saving")
        job_info = results_store.save(job_name, net_type, features, GSC, avgps, input_count, positive_genes, df_probs, df_GO, df_dis, df_convert_out, graph, df_edgelist)
        logging.info("job completed and output saved")

    except Exception as e:
        err_msg = "saving model error: " + str(e) 
        logging.error(err_msg)
        raise

    results_store.save_status(job_name, "complete")
    return True

def run_model(data_path, convert_IDs, net_type='String',features='Embedding', GSC='GO'):
    gp = geneplexus.GenePlexus(data_path, net_type, features, GSC)
    gp.load_genes(convert_IDs)
    mdl_weights, df_probs, avgps = gp.fit_and_predict()
    df_sim_go, df_sim_dis, weights_go, weights_dis = gp.make_sim_dfs()
    df_edgelist, isolated_genes, df_edge_sym, isolated_genes_sym = gp.make_small_edgelist()
    df_convert_out, positive_genes = gp.alter_validation_df()
    return df_probs, df_sim_go, df_sim_dis, avgps, df_edgelist, df_convert_out, positive_genes

def make_graph(df_edge, df_probs, max_num_genes = 50):
    df_edge.fillna(0)
    df_edge.columns = ['source', 'target', 'weight']
    nodes = df_probs[0:max_num_genes].copy()
    nodes = nodes.rename(columns={'Entrez': 'id', 'Class-Label': 'Class'})
    nodes = nodes.astype({'id': int})

    graph = {}
    graph["nodes"] = nodes.to_dict(orient='records')
    graph["links"] = df_edge.to_dict(orient='records')

    return graph

    