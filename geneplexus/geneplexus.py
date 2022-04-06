"""GenePlexus API."""
import logging
import os
import os.path as osp
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import pystow
import yaml

from . import _geneplexus
from ._config import config
from ._config import logger
from .download import download_select_data
from .exception import CustomNetworkError
from .util import check_param
from .util import normexpand


class GenePlexus:
    """The GenePlexus API class."""

    def __init__(
        self,
        file_loc: Optional[str] = None,
        net_type: config.NET_TYPE = "BioGRID",
        features: config.FEATURE_TYPE = "Embedding",
        gsc: config.GSC_TYPE = "GO",
        auto_download: bool = False,
        log_level: config.LOG_LEVEL_TYPE = "WARNING",
    ):
        """Initialize the GenePlexus object.

        Args:
            file_loc: Location of data files, if not specified, set to default
                ~/.data/geneplexus
            net_type: Type of network to use.
            features: Type of features of the network to use.
            gsc: Type of gene set collection to use for generating negatives.
            auto_download: Automatically download necessary files if set.
            log_level: Logging level.

        """
        logger.setLevel(logging.getLevelName(log_level))
        self.file_loc = file_loc  # type: ignore
        self.features = features
        self.gsc = gsc
        self.net_type = net_type
        self.log_level = log_level
        self.auto_download = auto_download
        self.input_genes: List[str] = []

        if self.auto_download:
            download_select_data(
                self.file_loc,
                "All",
                self.net_type,
                self.features,
                ["GO", "DisGeNet"],
                log_level=log_level,
            )

    @property
    def _params(self) -> List[str]:
        return [
            "file_loc",
            "net_type",
            "features",
            "gsc",
            "auto_download",
            "log_level",
            "input_genes",
        ]

    def dump_config(self, outdir: str):
        """Save parameters configuration to a config file."""
        params_dict = {i: getattr(self, i) for i in self._params}
        path = osp.join(outdir, "config.yaml")
        with open(path, "w") as f:
            yaml.dump(params_dict, f)
            logger.info(f"Config saved to {path}")

    @property
    def file_loc(self) -> str:
        """File location.

        Use default data location ~/.data/geneplexus if not set.

        """
        return self._file_loc

    @file_loc.setter
    def file_loc(self, file_loc: Optional[str]):
        if file_loc is None:
            self._file_loc = str(pystow.join("geneplexus"))
        else:
            self._file_loc = normexpand(file_loc)
        logger.info(f"Data direcory set to {self._file_loc}")

    @property
    def net_type(self) -> config.NET_TYPE:
        """Network to use."""
        return self._net_type  # type: ignore

    @net_type.setter
    def net_type(self, net_type: config.NET_TYPE):
        try:
            check_param("network", net_type, config.ALL_NETWORKS)
        except ValueError as e:
            # Check for custom network first
            data_files = os.listdir(self.file_loc)
            if f"NodeOrder_{net_type}.txt" in data_files:
                # Require feature file, gsc file, and gsc universe file
                features_fname = f"Data_{self.features}_{net_type}.npy"
                gsc_fname = f"GSC_{self.gsc}_{net_type}_GoodSets.json"
                universe_fname = f"GSC_{self.gsc}_{net_type}_universe.txt"
                if features_fname not in data_files:
                    raise CustomNetworkError(
                        f"Missing custom network feature data file {features_fname}, "
                        "set up using geneplexus.custom.edgelist_loc first.",
                    )
                elif gsc_fname not in data_files or universe_fname not in data_files:
                    raise CustomNetworkError(
                        f"Missing custom network GSC data files {gsc_fname} and/or {universe_fname}, "
                        "set up using geneplexus.custom.subset_gsc_to_network first.",
                    )
                else:
                    logger.info(f"Detected custom network {net_type!r}")
            else:
                raise e
        self._net_type = net_type

    @property
    def features(self) -> config.FEATURE_TYPE:
        """Features to use."""
        return self._features

    @features.setter
    def features(self, features: config.FEATURE_TYPE):
        check_param("feature", features, config.ALL_FEATURES)
        self._features = features

    @property
    def gsc(self) -> config.GSC_TYPE:
        """Geneset collection."""
        return self._gsc

    @gsc.setter
    def gsc(self, gsc: config.GSC_TYPE):
        check_param("GSC", gsc, config.ALL_GSCS)
        self._gsc = gsc

    def load_genes(self, input_genes: List[str]):
        """Load list of genes into the GenePlexus object.

        :attr:`GenePlexus.input_genes` (List[str]): Input gene list.

        Args:
            input_genes: Input genes, can be mixed type.

        See also:
            Use :meth:`geneplexus.util.read_gene_list` to load a gene list
            from a file.

        """
        input_genes = [item.upper() for item in input_genes]
        self.input_genes = input_genes

    def convert_to_Entrez(self):
        """Convert the loaded genes to Entrez.

        :attr:`GenePlexus.df_convert_out` (DataFrame)
            A table where the first column contains the original gene IDs, the
            second column contains the corresponding converted Entrez gene IDs.
            The rest of the columns are indicators of whether a given gene is
            present in any one of the networks.
        :attr:`GenePlexus.table_summary` (List[Dict[str, int]])
            List of netowrk stats summary dictionaries. Each dictionary has
            three keys: **Network**, **NetworkGenes**, and **PositiveGenes**
            (the number intersection between the input genes and the network
            genes).
        :attr:`GenePlexus.input_count` (int)
            Number of input genes.

        """
        self.convert_IDs, df_convert_out = _geneplexus._initial_ID_convert(self.input_genes, self.file_loc)
        self.df_convert_out, self.table_summary, self.input_count = _geneplexus._make_validation_df(
            df_convert_out,
            self.file_loc,
        )
        return self.df_convert_out

    def set_params(
        self,
        net_type: config.NET_TYPE,
        features: config.FEATURE_TYPE,
        gsc: config.GSC_TYPE,
    ):
        """Set GenePlexus parameters."""
        self.net_type = net_type
        self.features = features
        self.gsc = gsc

    def get_pos_and_neg_genes(self):
        """Set up positive and negative genes given the network.

        :attr:`GenePlexus.pos_genes_in_net` (array of str)
            Array of input gene Entrez IDs that are present in the network.
        :attr:`GenePlexus.genes_not_in_net` (array of str)
            Array of input gene Entrez IDs that are absent in the network.
        :attr:`GenePlexus.net_genes` (array of str)
            Array of network gene Entrez IDs.
        :attr:`GenePlexus.negative_genes` (array of str)
            Array of negative gene Entrez IDs derived using the input genes and
            the background gene set collection (GSC).

        """
        self.pos_genes_in_net, self.genes_not_in_net, self.net_genes = _geneplexus._get_genes_in_network(
            self.file_loc,
            self.net_type,
            self.convert_IDs,
        )
        self.negative_genes = _geneplexus._get_negatives(
            self.file_loc,
            self.net_type,
            self.gsc,
            self.pos_genes_in_net,
        )
        return self.pos_genes_in_net, self.negative_genes, self.net_genes

    def fit_and_predict(
        self,
        logreg_kwargs: Optional[Dict[str, Any]] = None,
        min_num_pos: int = 15,
        num_folds: int = 3,
        null_val: float = -10,
        random_state: Optional[int] = 0,
    ):
        """Fit a model and predict gene scores.

        Args:
            logreg_kwargs: Scikit-learn logistic regression settings (see
                :class:`~sklearn.linear_model.LogisticRegression`). If not set,
                then use the default logistic regression settings (l2 penalty,
                10,000 max iterations, lbfgs solver).
            min_num_pos: Minimum number of positives required for performing
                cross validation evaluation.
            num_folds: Number of cross validation folds.
            null_val: Null values to fill if cross validation was not able to
                be performed.
            random_state: Random state for reproducible shuffling stratified
                cross validation. Set to None for random.

        :attr:`GenePlexus.mdl_weights` (array of float)
            Trained model parameters.
        :attr:`GenePlexus.probs` (array of float)
            Genome wide gene prediction scores. A high value indicates the
            relevance of the gene to the input gene list.
        :attr:`GenePlexus.avgps` (array of float)
            Cross validation results. Performance is measured using
            log2(auprc/prior).
        :attr:`GenePlexus.df_probs` (DataFrame)
            A table with 7 columns: **Entrez** (the gene Entrez ID), **Symbol**
            (the gene Symbol), **Name** (the gene Name), **Probability** (the
            probability of a gene being part of the input gene list),
            **Known/Novel** (whether the gene is in the input gene list),
            **Class-Label** (positive, negative, or neutral), **Rank** (rank of
            relevance of the gene to the input gene list).

        """
        self.mdl_weights, self.probs, self.avgps = _geneplexus._run_SL(
            self.file_loc,
            self.net_type,
            self.features,
            self.pos_genes_in_net,
            self.negative_genes,
            self.net_genes,
            logreg_kwargs=logreg_kwargs,
            min_num_pos=min_num_pos,
            num_folds=num_folds,
            null_val=null_val,
            random_state=random_state,
        )
        self.df_probs = _geneplexus._make_prob_df(
            self.file_loc,
            self.net_genes,
            self.probs,
            self.pos_genes_in_net,
            self.negative_genes,
        )
        return self.mdl_weights, self.df_probs, self.avgps

    def make_sim_dfs(self):
        """Compute similarities bewteen the input genes and GO or DisGeNet.

        :attr:`GenePlexus.df_sim_GO` (DataFrame)
            A table with 4 columns: **ID** (the GO term ID), **Name** (name of
            the GO temr), **Similarity** (similarity between the input gene
            list and a GO term), **Rank** (rank of GO term similarity with the
            input gene list).
        :attr:`GenePlexus.df_sim_Dis` (DataFrame)
            A table with 4 columns: **ID** (the DO term ID), **Name** (name of
            the DO temr), **Similarity** (similarity between the input gene
            list and a DO term), **Rank** (rank of DO term similarity with the
            input gene list).
        :attr:`GenePlexus.weights_GO`
            Dictionary of pretrained model weights for GO. A key is a GO term,
            and the value is a dictionary with three keys: **Name** (name of
            the GO term), **Weights** (pretrained model weights), **PosGenes**
            (positive genes for this GO term).
        :attr:`GenePlexus.weights_Dis`
            Dictionary of pretrained model weights for DisGeNet. A key is a DO
            term, and the value is a dictionary with three keys: **Name** (name
            of the DO term), **Weights** (pretrained model weights),
            **PosGenes** (positive genes for this DO term).

        """
        self.df_sim_GO, self.df_sim_Dis, self.weights_GO, self.weights_Dis = _geneplexus._make_sim_dfs(
            self.file_loc,
            self.mdl_weights,
            self.gsc,
            self.net_type,
            self.features,
        )
        return self.df_sim_GO, self.df_sim_Dis, self.weights_GO, self.weights_Dis

    def make_small_edgelist(self, num_nodes: int = 50):
        """Make a subgraph induced by the top predicted genes.

        :attr:`GenePlexus.df_edge` (DataFrame)
            Table of edge list corresponding to the subgraph induced by the top
            predicted genes (in Entrez gene ID).
        :attr:`GenePlexus.isolated_genes` (List[str])
            List of top predicted genes (in Entrez gene ID) are are isolated
            from other top predicted genes in the network.
        :attr:`GenePlexus.df_edge_sym` (DataFrame)
            Table of edge list corresponding to the subgraph induced by the top
            predicted genes (in gene symbol).
        :attr:`GenePlexus.isolated_genes_sym` (List[str])
            List of top predicted genes (in gene symbol) are are isolated from
            other top predicted genes in the network.

        Args:
            num_nodes: Number of top genes to include.

        """
        self.df_edge, self.isolated_genes, self.df_edge_sym, self.isolated_genes_sym = _geneplexus._make_small_edgelist(
            self.file_loc,
            self.df_probs,
            self.net_type,
            num_nodes=num_nodes,
        )
        return self.df_edge, self.isolated_genes, self.df_edge_sym, self.isolated_genes_sym

    def alter_validation_df(self):
        """Make table about presence of input genes in the network.

        :attr:`df_convert_out_subset`
        :attr:`positive_genes`

        """
        self.df_convert_out_subset, self.positive_genes = _geneplexus._alter_validation_df(
            self.df_convert_out,
            self.table_summary,
            self.net_type,
        )
        return self.df_convert_out_subset, self.positive_genes
