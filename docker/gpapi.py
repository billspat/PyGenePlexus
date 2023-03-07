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

from pydantic import BaseModel, Field
from geneplexus import GenePlexus, config, util

##### types
GENESET = list[str]

sample_geneset = [
    "ARL6","BBS1","BBS10","BBS12","BBS2","BBS4","BBS5","BBS7","BBS9",
    "CCDC28B","CEP290","KIF7","MKKS","MKS1","TRIM32","TTC8","WDPCP",
]

class GPInput(BaseModel):
    """# model for input params to a GP model.  
    net_type can be overridden, but by default NETWORK env used by Docker GP
    """
    net_type: config.NET_TYPE = os.getenv('NETWORK')    
    features: config.FEATURE_TYPE 
    gsc: config.GSC_TYPE 
    geneset: GENESET = sample_geneset
    
  
class GPProb(BaseModel):
    Entrez: int
    Symbol: str
    Name: str
    Probability: float
    Known_Novel: str = Field(alias="Known/Novel") 
    Class_Label: str = Field(alias="Class-Label")
    Rank: int

 
class GPOutput(BaseModel):
    probs: list[GPProb]
    # sim_GO: pd.DataFrame
    # convert_out_subset: pd.DataFrame
    
    # class Config:
    #     arbitrary_types_allowed = True

class GPRunner():
    
    @classmethod
    def all_data_files_present(cls,file_loc):
        """validate presence of data files in folder"""
    
        if not os.path.exists(file_loc):
            return False
    
        for datafile in util.get_all_filenames():
            if not(os.path.exists(os.path.join(file_loc,datafile))):
                return False
    
        return True
    
    
    def __init__(self,file_loc:str):
        
        # validate backend data
        if not(GPRunner.all_data_files_present(file_loc)):
            raise Exception(f"backend data path not found or not complete in {file_loc}")
        
        self.file_loc = file_loc
        
    def run(self,gpinput:GPInput) -> GPOutput:
        gp = GenePlexus(self.file_loc, gpinput.net_type, gpinput.features, gpinput.gsc)
        gp.load_genes(gpinput.geneset)
        mdl_weights, df_probs, avgps = gp.fit_and_predict()
        
        # TODO these other steps are disabled until type model is added for the outputs
        # df_sim_GO, df_sim_Dis, weights_GO, weights_Dis = gp.make_sim_dfs()
        # # Return an edgelist
        # df_edge, isolated_genes, df_edge_sym, isolated_genes_sym = gp.make_small_edgelist(num_nodes=50)
        # # Return the validation datframwe for just the network that was used in the pipeline
        # df_convert_out_subset, positive_genes = gp.alter_validation_df()
        
        # for this first test, only output df_probs as a dictionary of records to be returned as JSON
        probs = df_probs.to_dict('records') 
        return(GPOutput(probs=probs) )


from fastapi import FastAPI

app = FastAPI()

# instantiate class to run the GP pipeline
gprunner = GPRunner(os.getenv('FILE_LOC'))

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
   


