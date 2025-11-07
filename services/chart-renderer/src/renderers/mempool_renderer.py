"""
Mempool fee distribution chart renderer
"""

import matplotlib.pyplot as plt
import numpy as np
from .base_renderer import BaseRenderer
from ..models import MempoolChartRequest
from ..config import settings


class MempoolRenderer(BaseRenderer):
    """Renderer for mempool fee distribution charts"""
    
    def render(self, request: MempoolChartRequest) -> bytes:
        """
        Render mempool fee distribution chart with quantile visualization
        
        Args:
            request: Mempool chart request data
            
        Returns:
            PNG image as bytes
        """
        fig, ax = self.create_figure(request.size)
        
        # Extract quantile data
        quantiles = ['p10', 'p25', 'p50', 'p75', 'p90']
        quantile_labels = ['10th', '25th', '50th', '75th', '90th']
        values = [request.fee_quantiles.get(q, 0) for q in quantiles]
        
        # Create bar chart with gradient effect
        mempool_color = settings.get_color("mempool")
        x_pos = np.arange(len(quantiles))
        
        bars = ax.bar(x_pos, values, color=mempool_color, alpha=0.8, 
                     edgecolor=mempool_color, linewidth=1.5)
        
        # Add value labels on top of bars
        for i, (bar, value) in enumerate(zip(bars, values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{self.format_sats_per_vbyte(value)}',
                   ha='center', va='bottom', color=self.text_color,
                   fontsize=9, fontweight='medium')
        
        # Add average fee line
        ax.axhline(y=request.avg_fee_rate, color=self.brand_color, 
                  linestyle='--', linewidth=2, alpha=0.7, 
                  label=f'Avg: {self.format_sats_per_vbyte(request.avg_fee_rate)} sat/vB')
        
        # Styling
        ax.set_xticks(x_pos)
        ax.set_xticklabels(quantile_labels)
        ax.set_xlabel('Fee Percentile', fontsize=10, color=self.text_color)
        ax.set_ylabel('Fee Rate (sat/vByte)', fontsize=10, color=self.text_color)
        
        # Title with context
        title = f'Mempool Fee Distribution'
        subtitle = f'Block {request.block_height:,} • {request.transaction_count:,} txs'
        self.add_title(ax, title, subtitle)
        
        # Legend
        ax.legend(loc='upper left', frameon=False, 
                 labelcolor=self.text_color, fontsize=9)
        
        # Tight layout
        fig.tight_layout()
        
        return self.render_to_bytes(fig)
