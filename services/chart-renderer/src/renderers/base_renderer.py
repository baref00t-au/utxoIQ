"""
Base chart renderer with common styling and utilities
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from typing import Tuple
from ..config import settings
from ..models import ChartSize


class BaseRenderer:
    """Base class for chart renderers with common styling"""
    
    def __init__(self):
        """Initialize renderer with brand styling"""
        self.bg_color = settings.get_color("background")
        self.surface_color = settings.get_color("surface")
        self.text_color = settings.get_color("text")
        self.grid_color = settings.get_color("grid")
        self.brand_color = settings.get_color("brand")
        
    def get_figure_size(self, size: ChartSize) -> Tuple[int, int]:
        """Calculate figure size based on chart size"""
        if size == ChartSize.MOBILE:
            width = settings.chart_mobile_width
        else:
            width = settings.chart_desktop_width
        
        height = int(width * settings.chart_height_ratio)
        return width, height
    
    def create_figure(self, size: ChartSize) -> Tuple[plt.Figure, plt.Axes]:
        """Create figure with brand styling"""
        width_px, height_px = self.get_figure_size(size)
        
        # Convert pixels to inches for matplotlib (at specified DPI)
        width_in = width_px / settings.chart_dpi
        height_in = height_px / settings.chart_dpi
        
        fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=settings.chart_dpi)
        
        # Apply dark theme styling
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.surface_color)
        
        # Style axes
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.grid_color)
        ax.spines['bottom'].set_color(self.grid_color)
        ax.spines['left'].set_linewidth(1)
        ax.spines['bottom'].set_linewidth(1)
        
        # Style ticks and labels
        ax.tick_params(colors=self.text_color, which='both', labelsize=9)
        ax.xaxis.label.set_color(self.text_color)
        ax.yaxis.label.set_color(self.text_color)
        
        # Grid styling
        ax.grid(True, alpha=0.15, color=self.grid_color, linewidth=0.5)
        ax.set_axisbelow(True)
        
        return fig, ax
    
    def format_datetime_axis(self, ax: plt.Axes, timestamps: list):
        """Format datetime axis with appropriate date formatting"""
        if len(timestamps) > 0:
            # Determine appropriate date format based on time range
            time_range = (timestamps[-1] - timestamps[0]).total_seconds()
            
            if time_range < 86400:  # Less than 1 day
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            elif time_range < 604800:  # Less than 1 week
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            
            # Rotate labels for better readability
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def add_title(self, ax: plt.Axes, title: str, subtitle: str = None):
        """Add title and optional subtitle to chart"""
        ax.set_title(title, color=self.text_color, fontsize=12, 
                    fontweight='semibold', pad=10, loc='left')
        
        if subtitle:
            ax.text(0, 1.05, subtitle, transform=ax.transAxes,
                   color=self.text_color, fontsize=9, alpha=0.7)
    
    def render_to_bytes(self, fig: plt.Figure) -> bytes:
        """Render figure to PNG bytes"""
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=settings.chart_dpi,
                   bbox_inches='tight', facecolor=self.bg_color,
                   edgecolor='none', pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    
    def format_btc(self, value: float) -> str:
        """Format BTC value with appropriate precision"""
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        elif abs(value) >= 1:
            return f"{value:,.2f}"
        else:
            return f"{value:.4f}"
    
    def format_sats_per_vbyte(self, value: float) -> str:
        """Format sats/vByte value"""
        return f"{value:.1f}"
