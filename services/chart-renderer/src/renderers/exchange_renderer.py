"""
Exchange flow chart renderer
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from .base_renderer import BaseRenderer
from ..models import ExchangeChartRequest
from ..config import settings


class ExchangeRenderer(BaseRenderer):
    """Renderer for exchange flow charts"""
    
    def render(self, request: ExchangeChartRequest) -> bytes:
        """
        Render exchange flow chart with timeline and volume indicators
        
        Args:
            request: Exchange chart request data
            
        Returns:
            PNG image as bytes
        """
        fig, ax = self.create_figure(request.size)
        
        exchange_color = settings.get_color("exchange")
        
        # Plot inflows and outflows as stacked area
        ax.fill_between(request.timestamps, 0, request.inflows,
                       color=exchange_color, alpha=0.6, label='Inflows')
        ax.fill_between(request.timestamps, 0, [-x for x in request.outflows],
                       color=self.brand_color, alpha=0.6, label='Outflows')
        
        # Plot net flow as line
        ax.plot(request.timestamps, request.net_flows,
               color=self.text_color, linewidth=2, alpha=0.9,
               label='Net Flow', marker='o', markersize=4)
        
        # Add zero line
        ax.axhline(y=0, color=self.grid_color, linestyle='-', 
                  linewidth=1, alpha=0.5)
        
        # Highlight spike if threshold provided
        if request.spike_threshold is not None:
            spike_indices = [i for i, flow in enumerate(request.inflows) 
                           if flow > request.spike_threshold]
            if spike_indices:
                spike_times = [request.timestamps[i] for i in spike_indices]
                spike_values = [request.inflows[i] for i in spike_indices]
                ax.scatter(spike_times, spike_values, color=self.brand_color,
                         s=100, marker='*', zorder=5, 
                         label=f'Spike (>{self.format_btc(request.spike_threshold)} BTC)')
        
        # Format datetime axis
        self.format_datetime_axis(ax, request.timestamps)
        
        # Styling
        ax.set_xlabel('Time', fontsize=10, color=self.text_color)
        ax.set_ylabel('Flow (BTC)', fontsize=10, color=self.text_color)
        
        # Title
        title = f'{request.entity_name} Exchange Flows'
        subtitle = f'{len(request.timestamps)} data points'
        self.add_title(ax, title, subtitle)
        
        # Legend
        ax.legend(loc='upper left', frameon=False,
                 labelcolor=self.text_color, fontsize=9)
        
        # Tight layout
        fig.tight_layout()
        
        return self.render_to_bytes(fig)
