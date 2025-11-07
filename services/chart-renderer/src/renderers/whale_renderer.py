"""
Whale accumulation chart renderer
"""

import matplotlib.pyplot as plt
import numpy as np
from .base_renderer import BaseRenderer
from ..models import WhaleChartRequest
from ..config import settings


class WhaleRenderer(BaseRenderer):
    """Renderer for whale accumulation charts"""
    
    def render(self, request: WhaleChartRequest) -> bytes:
        """
        Render whale accumulation chart with streak highlighting
        
        Args:
            request: Whale chart request data
            
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
        
        whale_color = settings.get_color("whale")
        
        # Top panel: Balance over time with accumulation highlighting
        ax1.plot(request.timestamps, request.balances,
                color=whale_color, linewidth=2.5, alpha=0.9)
        ax1.fill_between(request.timestamps, 0, request.balances,
                        color=whale_color, alpha=0.2)
        
        # Highlight accumulation periods (positive 7-day changes)
        accumulation_periods = []
        for i, change in enumerate(request.seven_day_changes):
            if change > 0:
                accumulation_periods.append(i)
        
        if accumulation_periods:
            # Group consecutive indices
            groups = []
            current_group = [accumulation_periods[0]]
            for i in range(1, len(accumulation_periods)):
                if accumulation_periods[i] == accumulation_periods[i-1] + 1:
                    current_group.append(accumulation_periods[i])
                else:
                    groups.append(current_group)
                    current_group = [accumulation_periods[i]]
            groups.append(current_group)
            
            # Highlight each accumulation period
            for group in groups:
                start_idx = group[0]
                end_idx = group[-1]
                ax1.axvspan(request.timestamps[start_idx],
                           request.timestamps[end_idx],
                           alpha=0.15, color=self.brand_color,
                           label='Accumulation' if group == groups[0] else '')
        
        ax1.set_ylabel('Balance (BTC)', fontsize=10, color=self.text_color)
        ax1.yaxis.label.set_color(self.text_color)
        
        # Bottom panel: 7-day changes
        colors = [whale_color if x >= 0 else self.brand_color 
                 for x in request.seven_day_changes]
        ax2.bar(request.timestamps, request.seven_day_changes,
               color=colors, alpha=0.7, width=0.8)
        
        # Add zero line
        ax2.axhline(y=0, color=self.grid_color, linestyle='-',
                   linewidth=1, alpha=0.5)
        
        ax2.set_ylabel('7-Day Change (BTC)', fontsize=10, color=self.text_color)
        ax2.yaxis.label.set_color(self.text_color)
        
        # Format datetime axis
        self.format_datetime_axis(ax2, request.timestamps)
        ax2.set_xlabel('Time', fontsize=10, color=self.text_color)
        ax2.xaxis.label.set_color(self.text_color)
        
        # Title on top panel
        title = f'Whale Accumulation'
        address_short = f'{request.address[:8]}...{request.address[-6:]}'
        subtitle = f'{address_short} • {request.accumulation_streak_days} day streak'
        ax1.set_title(title, color=self.text_color, fontsize=12,
                     fontweight='semibold', pad=10, loc='left')
        ax1.text(0, 1.05, subtitle, transform=ax1.transAxes,
                color=self.text_color, fontsize=9, alpha=0.7)
        
        # Legend
        if accumulation_periods:
            ax1.legend(loc='upper left', frameon=False,
                      labelcolor=self.text_color, fontsize=9)
        
        # Tight layout
        fig.tight_layout()
        
        return self.render_to_bytes(fig)
