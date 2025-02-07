# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_config.ipynb.

# %% auto 0
__all__ = ['L402_VERSION']

# %% ../nbs/02_config.ipynb 2
from fastcore.all import *
from fastcore.xdg import *

# %% ../nbs/02_config.ipynb 3
_l402_home_dir = 'l402' # sub-directory of xdg base dir
_l402_db_name = 'l402.db'

# %% ../nbs/02_config.ipynb 4
def _db_path(): 
    p =  xdg_config_home() / _l402_home_dir / _l402_db_name
    p.parent.mkdir(exist_ok=True)
    return p

# %% ../nbs/02_config.ipynb 7
L402_VERSION = '0.2.2'
