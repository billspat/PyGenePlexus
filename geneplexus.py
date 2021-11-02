import argparse
import utls
import numpy as np


'''

1. Don't know what to do with different input types, right now hard coded in
2. How to save outputs or store them for best use in cloud
3. How to get this to run on command line (i.e. geneplexus -t validate)
4. Can we make a repo/package that is good for cloud and stand alone version

'''

parser = argparse.ArgumentParser()
parser.add_argument('-t','--task',
                    default = 'run_model',
                    type = str,
                    help = 'options are validate or run_model')
parser.add_argument('-i','--input',
                    default = 'input_genes.txt',
                    type = str,
                    help = 'file path to the gene functions')
parser.add_argument('-fl','--file_loc',
                    default = 'HPCC',
                    type = str,
                    help = 'options local, HPCC, cloud')
parser.add_argument('-n','--net_type',
                    default = 'BioGRID',
                    type = str,
                    help = 'options are BioGRID, STRING-EXP, STRING, GIANT-TN')
parser.add_argument('-f','--features',
                    default = 'Embedding',
                    type = str,
                    help = 'options are Embedding, Adjacency, Influence')
parser.add_argument('-g','--GSC',
                    default = 'GO',
                    type = str,
                    help = 'options are GO, DisGeNet')
parser.add_argument('-c','--CV',
                    default = 'doCV',
                    type = str,
                    help = 'options are doCV or noCV')

args = parser.parse_args()


if args.task == 'validate':
    input_genes = np.loadtxt(args.input,dtype=str,delimiter=', ')
    input_genes = [item.strip("'") for item in input_genes]
    convert_IDs, df_convert_out = utls.intial_ID_convert(input_genes,file_loc=args.file_loc)
    df_convert_out, df_summary = utls.make_validation_df(df_convert_out,file_loc=args.file_loc)
    # Print some Validaton landing page outputs
    print(df_summary)
    print(df_convert_out)

elif args.task == 'run_model':
    input_genes = np.loadtxt(args.input,dtype=str,delimiter=', ')
    input_genes = [item.strip("'") for item in input_genes]
    convert_IDs, df_convert_out = utls.intial_ID_convert(input_genes,file_loc=args.file_loc)
    pos_genes_in_net, genes_not_in_net, net_genes = utls.get_genes_in_network(convert_IDs,args.net_type,file_loc=args.file_loc)
    negative_genes = utls.get_negatives(pos_genes_in_net,args.net_type,args.GSC,file_loc=args.file_loc)
    mdl_weights, probs, avgps = utls.run_SL(pos_genes_in_net,negative_genes,net_genes,
                                            args.net_type,args.features,args.CV,file_loc=args.file_loc)
    df_probs, Entrez_to_Symbol = utls.make_prob_df(net_genes,probs,pos_genes_in_net,negative_genes,file_loc=args.file_loc)
    df_GO, df_dis, weights_dict_GO, weights_dict_Dis = utls.make_sim_dfs(mdl_weights,args.GSC,
                                                                         args.net_type,args.features,file_loc=args.file_loc)
    df_edge, isolated_genes, df_edge_sym, isolated_genes_sym = utls.make_small_edgelist(df_probs,args.net_type,
                                                                                        Entrez_to_Symbol,
                                                                                        file_loc=args.file_loc)
    # Print some probability landing page  outputs
    print(df_probs.head)
    # Print some sim 
    print(df_GO.head())
    print(df_dis.head())
    # print some edges that could be used in network figure
    print(df_edge_sym.head())