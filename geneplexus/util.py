import json
import os.path as osp
from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional

import numpy as np

from . import config


def mapgene(gene: str, entrez_to_symbol: Dict[str, List[str]]) -> str:
    """Map entrez to other representations.

    Args:
        gene (str): Entrez gene ID.
        entrez_to_symbol (Dict[str, List[str]]): Mapping from Entrez to list of
            gene symbols.

    Returns:
        str: Gene symbol corresponding to the gene entrez ID.

    Note:
        Multiple symbols is allowed, separated by '/'.

    """
    try:
        syms = "/".join(entrez_to_symbol[gene])
    except KeyError:
        syms = "N/A"
    return syms


def get_all_filenames():
    """Iterate over filenames."""
    with open(config.DATA_FILENAMES_PATH, "r") as f:
        for line in f:
            yield line.strip()


def check_file(path: str):
    """Check existence of a file.

    Args:
        path (str): Path to the file.

    Raises:
        FileNotFoundError: if file not exist.

    """
    if not osp.isfile(path):
        raise FileNotFoundError(path)


def read_gene_list(
    path: str,
    sep: Optional[str] = ", ",
) -> List[str]:
    """Read gene list from flie.

    Args:
        path (str): Path to the input gene list file.
        sep (str): Seperator between genes.

    """
    if sep == "newline":
        sep = None
    elif sep == "tab":
        sep = "\t"
    return [gene.strip("'") for gene in open(path, "r").read().split(sep)]


def _load_json_file(file_loc: str, file_name: str) -> Dict[str, Any]:
    file_path = osp.join(file_loc, file_name)
    check_file(file_path)
    return json.load(open(file_path, "rb"))


def load_geneid_conversion(
    file_loc: str,
    src_id_type: config.ID_SRC_TYPE,
    dst_id_type: config.ID_DST_TYPE,
    upper: bool = False,
) -> config.ID_CONVERSION_MAP_TYPE:
    """Load the gene ID conversion mapping.

    Args:
        file_loc (str): Directory containig the ID conversion file.
        src_id_type (ID_SRC_TYPE): Souce gene ID type.
        dst_id_type (ID_DST_TYPE): Destination gene ID type.
        upper (bool): If set to True, then convert all keys to upper case.

    """
    if (src_id_type, dst_id_type) not in config.VALID_ID_CONVERSION:
        raise ValueError(f"Invalid ID conversion from {src_id_type} to {dst_id_type}")

    file_name = f"IDconversion_Homo-sapiens_{src_id_type}-to-{dst_id_type}.json"
    conversion_map = _load_json_file(file_loc, file_name)

    if upper:
        conversion_map = {src.upper(): dst for src, dst in conversion_map.items()}

    return conversion_map


def load_gsc(
    file_loc: str,
    GSC: config.GSC_TYPE,
    net_type: config.NET_TYPE,
) -> config.GSC_DATA_TYPE:
    """Load gene set collection dictionary."""
    file_name = f"GSC_{GSC}_{net_type}_GoodSets.json"
    return _load_json_file(file_loc, file_name)


def load_pretrained_weights(
    file_loc: str,
    target_set: config.GSC_TYPE,
    net_type: config.NET_TYPE,
    features: config.FEATURE_TYPE,
) -> config.PRETRAINED_DATA_TYPE:
    """Load pretrained model dictionary."""
    file_name = f"PreTrainedWeights_{target_set}_{net_type}_{features}.json"
    return _load_json_file(file_loc, file_name)


def _load_np_file(
    file_loc: str,
    file_name: str,
    load_method: Literal["npy", "txt"],
) -> np.ndarray:
    """Check np file existence and load."""
    file_path = osp.join(file_loc, file_name)
    check_file(file_path)

    if load_method == "npy":
        return np.load(file_path)
    elif load_method == "txt":
        return np.loadtxt(file_path, dtype=str)
    else:
        raise ValueError(f"Unknwon load method: {load_method!r}")


def load_node_order(file_loc: str, net_type: config.NET_TYPE) -> np.ndarray:
    """Load network genes."""
    file_name = f"NodeOrder_{net_type}.txt"
    return _load_np_file(file_loc, file_name, load_method="txt")


def load_genes_universe(
    file_loc: str,
    GSC: config.GSC_TYPE,
    net_type: config.NET_TYPE,
) -> np.ndarray:
    """Load gene universe a given network and GSC."""
    file_name = f"GSC_{GSC}_{net_type}_universe.txt"
    return _load_np_file(file_loc, file_name, load_method="txt")


def load_gene_features(
    file_loc: str,
    features: config.FEATURE_TYPE,
    net_type: config.NET_TYPE,
) -> np.ndarray:
    """Load gene features."""
    file_name = f"Data_{features}_{net_type}.npy"
    return _load_np_file(file_loc, file_name, load_method="npy")


def load_correction_order(
    file_loc: str,
    target_set: config.GSC_TYPE,
    net_type: config.NET_TYPE,
) -> np.ndarray:
    """Load correction matrix order."""
    file_name = f"CorrectionMatrixOrder_{target_set}_{net_type}.txt"
    return _load_np_file(file_loc, file_name, load_method="txt")


def load_correction_mat(
    file_loc: str,
    GSC: config.GSC_TYPE,
    target_set: config.GSC_TYPE,
    net_type: config.NET_TYPE,
    features: config.FEATURE_TYPE,
) -> np.ndarray:
    """Load correction matrix."""
    file_name = f"CorrectionMatrix_{GSC}_{target_set}_{net_type}_{features}.npy"
    return _load_np_file(file_loc, file_name, load_method="npy")
