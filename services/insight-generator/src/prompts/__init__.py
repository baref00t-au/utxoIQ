"""Prompt templates for AI insight generation"""

from .mempool_prompt import MEMPOOL_TEMPLATE
from .exchange_prompt import EXCHANGE_TEMPLATE
from .miner_prompt import MINER_TEMPLATE
from .whale_prompt import WHALE_TEMPLATE
from .treasury_prompt import TREASURY_TEMPLATE
from .predictive_prompt import PREDICTIVE_TEMPLATE

__all__ = [
    'MEMPOOL_TEMPLATE',
    'EXCHANGE_TEMPLATE',
    'MINER_TEMPLATE',
    'WHALE_TEMPLATE',
    'TREASURY_TEMPLATE',
    'PREDICTIVE_TEMPLATE',
]
