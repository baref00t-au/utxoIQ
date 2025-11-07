"""
Predictive signal chart renderer
"""

import matplotlib.pyplot as plt
import numpy as np
from .base_renderer import BaseRenderer
from ..models import PredictiveChartRequest
from ..config import settings


class PredictiveRenderer(BaseRenderer):
    """Renderer for predictive signal charts"""
    
    def render(self, request: PredictiveChartRequest) -> bytes:
        """
        Render predictive signal chart with confidence intervals
        
        Args:
            request: Predictive chart request data
            
        Returns:
            PNG image as bytes
        """
        fig, ax = self.create_figure(request.size)
        
        # Split timestamps into historical and predicted
        split_idx = len(request.historical_values)
        historical_times = request.timestamps[:split_idx]
        predicted_times = request.timestamps[split_idx-1:]  # Overlap last point
        
        # Plot historical data
        ax.plot(historical_times, request.historical_values,
               color=self.text_color, linewidth=2.5, alpha=0.9,
               label='Historical', marker='o', markersize=4)
        
        # Plot predicted data
        predicted_values_with_overlap = [request.historical_values[-1]] + request.predicted_values
        ax.plot(predicted_times, predicted_values_with_overlap,
               color=self.brand_color, linewidth=2.5, alpha=0.9,
               linestyle='--', label='Forecast', marker='s', markersize=4)
        
        # Plot confidence intervals
        if request.confidence_intervals:
            lower_bounds = [ci[0] for ci in request.confidence_intervals]
            upper_bounds = [ci[1] for ci in request.confidence_intervals]
            
            # Add overlap point from historical
            lower_with_overlap = [request.historical_values[-1]] + lower_bounds
            upper_with_overlap = [request.historical_values[-1]] + upper_bounds
            
            ax.fill_between(predicted_times, lower_with_overlap, upper_with_overlap,
                           color=self.brand_color, alpha=0.2,
                           label='Confidence Interval')
        
        # Add vertical line at prediction boundary
        if len(historical_times) > 0:
            ax.axvline(x=historical_times[-1], color=self.grid_color,
                      linestyle=':', linewidth=2, alpha=0.5)
        
        # Format datetime axis
        self.format_datetime_axis(ax, request.timestamps)
        
        # Styling
        ax.set_xlabel('Time', fontsize=10, color=self.text_color)
        ax.set_ylabel('Value', fontsize=10, color=self.text_color)
        
        # Title
        title = f'{request.signal_type.replace("_", " ").title()} Forecast'
        subtitle = f'Horizon: {request.forecast_horizon}'
        self.add_title(ax, title, subtitle)
        
        # Legend
        ax.legend(loc='upper left', frameon=False,
                 labelcolor=self.text_color, fontsize=9)
        
        # Tight layout
        fig.tight_layout()
        
        return self.render_to_bytes(fig)
