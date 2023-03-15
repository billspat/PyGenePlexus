# gpapi.py : http interface to geneplexus
# version 1 PSB, 
#  - requires all data files to be present as data files are checked at startup
#  - allows running with any network (not tied to one network or the other)
#  - runs GP in foreground so response is not given until GP is complete


import os, sys
import os.path as osp
import pathlib

import pandas as pd

from typing import Union, Literal
from pydantic import BaseModel, Field
from fastapi import FastAPI

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

# Entrez	Symbol	Name	Probability	Known/Novel	Class-Label	Rank
class GPprob(BaseModel):
    Entrez: str
    Symbol: str
    Name: str
    Probability: float
    Known_Novel: str  = Field(alias="Known/Novel") 
    Class_Label: str  = Field(alias="Class-Label")
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

class GPsimDis(BaseModel):
    # example data
    # 610  DOID:0110123  Bardet-Biedl syndrome 1   17.175403     1
     ID_: str  = Field(alias = "ID")
     Name: str
     Similarity: float
     Rank: int

class GPconvertOut(BaseModel):
    """ element of data frame """
    # example data
    #  Original ID Entrez ID In BioGRID?
    # 0        ARL6     84100           Y

    # using question mark causes problem with typing and API, so not using 
    # it here, and requires the GP 
    original_id: str = Field(alias = "Original ID")
    entrez_id: int = Field(alias = "Entrez ID")
    in_network: Literal['Y', 'N'] = Field(alias = "In Network")
     
class GPOutput(BaseModel):
    probs: list[GPprob]
    edge_list: list[GPedge]
    sim_go: list[GPsimGo]
    avgps: list[float] 
    sim_dis: list[GPsimDis]
    convert_out: list[GPconvertOut]
    positive_genes: int



####### functionality  


def all_data_files_present(file_loc:str)->bool:
    """validate presence of data files in folder"""
    #TODO add network param and only look for common files and net-specific files

    if not os.path.exists(file_loc):
        return False

    for datafile in util.get_all_filenames():
        if not(os.path.exists(os.path.join(file_loc,datafile))):
            return False

    return True

class GPRunner():
    """ class to run GP, collect outputs and create graph structure"""

    def __init__(self,file_loc:str, net_type:config.NET_TYPE):
        
        self.status = ""
        self.set_status("validating backend data")
        # # validate backend data
        # if not(all_data_files_present(file_loc)):
        #     raise Exception(f"backend data path not found or not complete in {file_loc}")
        
        self.file_loc = file_loc
        self.net_type = net_type
        

    def set_status(self,status_msg:str):
        self.status = status_msg
        print(status_msg) 

    def run(self,gpinput:GPInput) -> GPOutput:
        """run the whole GP pipeline.  Alter outputs to make them API/JSON friendly"""
        
        # if no net_type is sent, use class property to set it 
        if not gpinput.net_type:
            gpinput.net_type = self.net_type
        self.set_status(status_msg=f"starting GP with {net_type}")
        
        gp = GenePlexus(self.file_loc, 
                        gpinput.net_type, 
                        gpinput.features, 
                        gpinput.gsc
                        )
        
        # load genes on separate process for profiling and debugging
        self.set_status(status_msg=f"loading geneset")
        gp.load_genes(gpinput.geneset)
        
        self.set_status(status_msg=f"loaded {len(gpinput.geneset)} genes")
        
        # GP pipeline
        self.set_status(status_msg=f"calculating model weights")

        mdl_weights, df_probs, avgps = gp.fit_and_predict()
        self.set_status(status_msg=f"make_sim_dfs")
        df_sim_go, df_sim_dis, weights_go, weights_dis = gp.make_sim_dfs()
        self.set_status(status_msg=f"make edgelist")

        df_edgelist, isolated_genes, df_edge_sym, isolated_genes_sym = gp.make_small_edgelist()
        self.set_status(status_msg=f"make gene list")
        df_convert_out, positive_genes = gp.alter_validation_df()
        
        # convert data frames to dictionaries for type checking and 
        # fix column names as needed to make it api/JSON friendly        
        self.set_status(status_msg=f"preparing output")
        df_convert_out.columns = ["Original ID","Entrez ID","In Network"]

        return(GPOutput(
                    probs=df_probs.to_dict('records'),
                    sim_go = df_sim_go.to_dict('records'), 
                    edge_list=df_edgelist.to_dict('records'),
                    sim_dis = df_sim_dis.to_dict('records'),
                    avgps = avgps, 
                    convert_out = df_convert_out.to_dict('records'),
                    positive_genes = positive_genes
                    )
                )


######### api
app = FastAPI()

# instantiate class to run the GP pipeline
# TODO remove the defaults here and deal with no network set (e.g. not network specific)
net_type = os.getenv('NETWORK') or 'BioGRID'
file_loc = os.getenv('FILE_LOC') or '../.data'
# TODO data check

all_data_files_present(file_loc)

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