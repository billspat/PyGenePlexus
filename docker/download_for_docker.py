#!/usr/bin/env python3
"""Download  """

# you must install geneplexus prior to running this files 
import os, sys
import pathlib
import geneplexus
import logging


def default_datadir():
    homedir = pathlib.Path(__file__).absolute().parent.parent
    datadir = os.path.join(homedir, ".data")
    return(datadir)

def dl(net, feat, datadir=None):
    
    if not(datadir):
        datadir = default_datadir()
        
    """download for specific network and feature from standard doi"""
    try:
        geneplexus.download.download_select_data(
            datadir,
            tasks="All",
            networks=net,
            features=feat,
            gscs=["GO", "DisGeNet"],
        )
        return True
    
    except Exception as e:
        logging.logger(f"download exception: {e}")
        return False


if __name__ == '__main__':
    nets = geneplexus.config.ALL_NETWORKS
    
    import argparse
    
    parser = argparse.ArgumentParser("download_for_docker.py")
    parser.add_argument('network', nargs='*', default=geneplexus.config.ALL_NETWORKS, 
                        help="List of networks from those available, or blank for all networks")
    parser.add_argument('-d', '--datadir', metavar='/path/to/.data', help="optional directory to store gp data, overrides env var 'FILE_LOC'")
    
    # allow for single command line argument 
    args = parser.parse_args()
    nets = set(args.network)
    
    if args.datadir:
        datadir = args.datadir
    elif os.getenv('FILE_LOC'):
        datadir = os.getenv('FILE_LOC')
    else:
        datadir = default_datadir()   
    
    os.makedirs(datadir, exist_ok=True)

    if not (nets <= set(geneplexus.config.ALL_NETWORKS)):
        print(f"the command line {nets} includes and invalid network ")
        print(f" valid networks: {geneplexus.config.ALL_NETWORKS}")
        sys.exit()

    print(f"downloading for networks {nets} into {datadir}")
        
    for net in nets: 
        for feat in geneplexus.config.ALL_FEATURES:
            downloaded = dl(net, feat, datadir)
            if not downloaded:
                raise Exception(f"barfed on {net} {feat}")