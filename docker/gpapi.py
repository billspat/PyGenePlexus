# gpapi.py : http interface to geneplexus
# this simply wraps fast api around the main gp data pipeline
# version 1 PSB, 
#  - requires all data files to be present as data files are checked at startup
#  - allows running with any network (not tied to one network or the other)
#  - runs GP in foreground so response is not given until GP is complete


import os, sys
import os.path as osp
import pathlib

import pandas as pd

from typing import Union
from pydantic import BaseModel, Field
from geneplexus import GenePlexus, config, util

############ types
GENESET = list[str]

sample_geneset = [
    "ARL6","BBS1","BBS10","BBS12","BBS2","BBS4","BBS5","BBS7","BBS9",
    "CCDC28B","CEP290","KIF7","MKKS","MKS1","TRIM32","TTC8","WDPCP",
]

class GPInput(BaseModel):
    """# model for input params to a GP model.  
    net_type is optional so a pre-set value can be used can be overridden
    When using inside network-specific docker image, don't set net_type when creating types
    """
    # allow net_type to be empty, and if so use a pre-set net type when running the pipeline
    net_type: Union[config.NET_TYPE, None] = None   
    features: config.FEATURE_TYPE 
    gsc: config.GSC_TYPE 
    geneset: GENESET = sample_geneset

class GPprob(BaseModel):
    " also use for node types"
    Entrez: int
    Symbol: str
    Name: str
    Probability: float
    Known_Novel: str = Field(alias="Known/Novel") 
    Class_Label: str = Field(alias="Class-Label")
    Rank: int

class GPedge(BaseModel):
    Node1:int
    Node2:int
    Weight:int
    
    
class GPsimGo(BaseModel):
    # example data: 'GO:0070202', 'regulation of establishment of protein localization to chromosome', '5.021538922627177', '1'      
    ID:str
    Name:str
    Similarity:float
    Rank:int

class GPOutput(BaseModel):
    probs: list[GPprob]
    sim_go: list[GPsimGo]
    edge_list: list[GPedge]
    # sim_dis, 
    # avgps, 
    # edgelist, 
    # convert_out, 
    # positive_genes,
    # graph?
    class Config:
         arbitrary_types_allowed = True


####### functionality  
class GPRunner():
    """ class to run GP, collect outputs and create graph structure"""
    @classmethod
    def all_data_files_present(cls,file_loc:str)->bool:
        """validate presence of data files in folder"""
    
        if not os.path.exists(file_loc):
            return False
    
        for datafile in util.get_all_filenames():
            if not(os.path.exists(os.path.join(file_loc,datafile))):
                return False
    
        return True
    
    def __init__(self,file_loc:str, net_type:config.NET_TYPE):
        
        # validate backend data
        if not(GPRunner.all_data_files_present(file_loc)):
            raise Exception(f"backend data path not found or not complete in {file_loc}")
        
        self.file_loc = file_loc
        self.net_type = net_type
        
    def run(self,gpinput:GPInput) -> GPOutput:
        # if no net_type is sent, use class property
        gp = GenePlexus(self.file_loc, 
                        gpinput.net_type or self.net_type, 
                        gpinput.features, 
                        gpinput.gsc
                        )
        
        # load genes on separate process for profiling and debugging
        gp.load_genes(gpinput.geneset)
        mdl_weights, df_probs, avgps = gp.fit_and_predict()
        df_sim_go, df_sim_dis, weights_go, weights_dis = gp.make_sim_dfs()
        df_edgelist, isolated_genes, df_edge_sym, isolated_genes_sym = gp.make_small_edgelist()
        df_convert_out, positive_genes = gp.alter_validation_df()

        return(GPOutput(probs=df_probs.to_dict('records'), 
                        sim_go = df_sim_go.to_dict('records'), 
                        edge_list=df_edgelist.to_dict('records'),
                        # sim_dis, 
                        # avgps, 
                        # df_convert_out, 
                        # positive_genes,
                        # graph = make_graph(df_edgelist, df_probs)
                        )
        )


######### api
from fastapi import FastAPI

app = FastAPI()

# instantiate class to run the GP pipeline
# doing this here limits the network to one type for the entire run
net_type = os.getenv('NETWORK') or 'BioGRID'
file_loc = os.getenv('FILE_LOC') or '../.data'

gprunner = GPRunner(file_loc, net_type)

@app.get("/")
async def root():
    """simple response to confirm server is running"""
    return {"message": "GenePlexus App"}
 
@app.post("/check/") 
async def check(gpinput: GPInput) -> GPInput:
    """ mirror the input to check that the server is accepting input"""
    return(gpinput)
    
    
@app.post("/run/")
async def run(gpinput: GPInput) -> GPOutput:
    """run the GP pipeline for input parameters and geneset"""
    gpoutput = gprunner.run(gpinput)
    return(gpoutput)
   


#### saved but unused
#TODO remove this step from here, and instead rename columns for edgelist structure

class GPgraphlink(BaseModel):
    source: int
    target: int
    weight: int
    
class GPgraphnode(BaseModel):
    """this is the same as probs with columns renamed for D3 viz library.  It has some unfortunate element 
    names that are python reserved words.  """
    id_: int = Field(alias="id")
    class_ : str = Field(alias="class")
    Symbol: str
    Name: str
    Probability: float
    Known_Novel: str = Field(alias="Known/Novel") 
    Rank: int


class GPgraph(BaseModel):
    nodes: list[GPgraphnode]
    links: list[GPgraphlink]

def make_graph(df_edgelist, df_probs, max_num_genes:int = 50) -> GPgraph:
    """create data structure with names easier for D3 network viz"""
    # needed for D3 inside Javascript from edgelist and probs outputs
    edges = df_edgelist.copy().fillna(0)
    
    # rename colums of edges and nodes for D3
    edges.columns = ['source', 'target', 'weight']
    nodes = df_probs[0:max_num_genes].copy()
    nodes = nodes.rename(columns={'Entrez': 'id', 'Class-Label': 'Class'})
    nodes = nodes.astype({'id': int})
    
    graph = {"nodes": nodes.to_dict(orient='records'), 
                "links": df_edgelist.to_dict(orient='records')
            }
    
    return graph