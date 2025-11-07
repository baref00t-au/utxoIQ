"""
Miner treasury chart renderer
"""

import matplotlib.pyplot as plt
import numpy as np
from .base_renderer import BaseRenderer
from ..models import MinerChartRequest
from ..config import settings


class MinerRenderer(BaseRenderer):
    """Renderer for miner treasury charts"""
    
    def render(self, request: MinerChartRequest) -> bytes:
        """
        Render miner treasury chart with balance change visualization
        
        Args:
            request: Miner chart request data
            
        Returns:
            PNG image as bytes
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(
            self.get_figure_size(request.size)[0] / settings.chart_dpi,
            self.get_figure_size(request.size)[1] / settings.chart_dpi * 1.5
        ), dpi=settings.chart_dpi, sharex=True)
        
        # Apply styling to both axes
        for ax in [ax1, ax2]:
            fig.patch.set_facecolor(self.bg_color)
            ax.set_facecolor(self.surface_color)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(self.grid_color)
            ax.spines['bottom'].set_color(self.grid_color)
            ax.tick_params(colors=self.text_color, which='both', labelsize=9)
            ax.grid(True, alpha=0.15, color=self.grid_color, linewidth=0.5)
            ax.set_axisbelow(True)
        
        miner_color = settings.get_color("miner")
        
        # Top panel: Balance over time
        ax1.plot(request.timestamps, request.balances,
                color=miner_color, linewidth=2.5, alpha=0.9)
        ax1.fill_between(request.timestamps, 0, request.balances,
                        color=miner_color, alpha=0.2)
        
        ax1.set_ylabel('Balance (BTC)', fontsize=10, color=self.text_color)
        ax1.yaxis.label.set_color(self.text_color)
        
        # Bottom panel: Daily changes as bar chart
        colors = [miner_color if x >= 0 else self.brand_color 
                 for x in request.daily_changes]
        ax2.bar(request.timestamps, request.daily_changes,
               color=colors, alpha=0.7, width=0.8)
        
        # Add zero line
        ax2.axhline(y=0, color=self.grid_color, linestyle='-',
                   linewidth=1, alpha=0.5)
        
        ax2.set_ylabel('Daily Change (BTC)', fontsize=10, color=self.text_color)
        ax2.yaxis.label.set_color(self.text_color)
        
        # Format datetime axis
        self.format_datetime_axis(ax2, request.timestamps)
        ax2.set_xlabel('Time', fontsize=10, color=self.text_color)
        ax2.xaxis.label.set_color(self.text_color)
        
        # Title on top panel
        title = f'{request.entity_name} Treasury'
        current_balance = request.balances[-1] if request.balances else 0
        subtitle = f'Current: {self.format_btc(current_balance)} BTC'
        ax1.set_title(title, color=self.text_color, fontsize=12,
                     fontweight='semibold', pad=10, loc='left')
        ax1.text(0, 1.05, subtitle, transform=ax1.transAxes,
                color=self.text_color, fontsize=9, alpha=0.7)
        
        # Tight layout
        fig.tight_layout()
        
        return self.render_to_bytes(fig)
