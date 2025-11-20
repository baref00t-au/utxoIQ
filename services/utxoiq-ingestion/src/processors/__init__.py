"""
Signal processors package
"""

# Always export base classes
from .base_processor import SignalProcessor, ProcessorConfig, ProcessingContext

# Lazy-load processor implementations to avoid importing heavy dependencies
# unless explicitly needed
def _get_processors():
    """Lazy-load all processor implementations."""
    from .mempool_processor import MempoolProcessor
    from .exchange_processor import ExchangeProcessor
    from .miner_processor import MinerProcessor
    from .whale_processor import WhaleProcessor
    from .treasury_processor import TreasuryProcessor
    from .predictive_analytics import PredictiveAnalyticsModule
    
    return {
        "MempoolProcessor": MempoolProcessor,
        "ExchangeProcessor": ExchangeProcessor,
        "MinerProcessor": MinerProcessor,
        "WhaleProcessor": WhaleProcessor,
        "TreasuryProcessor": TreasuryProcessor,
        "PredictiveAnalyticsModule": PredictiveAnalyticsModule
    }

# Export base classes by default
__all__ = [
    "SignalProcessor",
    "ProcessorConfig",
    "ProcessingContext",
    "_get_processors"  # For lazy loading
]

# Allow direct imports if needed (but will trigger dependency loading)
def __getattr__(name):
    """Lazy-load processor classes on demand."""
    processors = _get_processors()
    if name in processors:
        return processors[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
