"""Email template generation using Jinja2."""
from jinja2 import Environment, BaseLoader
from typing import List
from datetime import datetime

from .models import DailyBrief, Insight
from .config import settings


class EmailTemplates:
    """Email template generator."""
    
    def __init__(self):
        """Initialize template environment."""
        self.env = Environment(loader=BaseLoader())
    
    def render_daily_brief(self, brief: DailyBrief, user_id: str) -> str:
        """Render daily brief email template."""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>utxoIQ Daily Brief - {{ date }}</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #0B0B0C;
            color: #F4F4F5;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 32px 0;
            border-bottom: 1px solid #2A2A2E;
        }
        .logo {
            font-size: 24px;
            font-weight: 600;
            color: #FF5A21;
        }
        .subtitle {
            font-size: 14px;
            color: #A1A1AA;
            margin-top: 8px;
        }
        .content {
            padding: 32px 0;
        }
        .date-header {
            font-size: 13px;
            color: #A1A1AA;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 16px;
        }
        .insight-card {
            background-color: #131316;
            border: 1px solid #2A2A2E;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .insight-header {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        .signal-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .signal-dot.mempool { background-color: #FB923C; }
        .signal-dot.exchange { background-color: #38BDF8; }
        .signal-dot.miner { background-color: #10B981; }
        .signal-dot.whale { background-color: #8B5CF6; }
        .signal-type {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #A1A1AA;
            margin-right: 12px;
        }
        .confidence-badge {
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 8px;
            font-weight: 500;
        }
        .confidence-high {
            background-color: rgba(16, 185, 129, 0.2);
            color: #10B981;
        }
        .confidence-medium {
            background-color: rgba(217, 119, 6, 0.2);
            color: #D97706;
        }
        .insight-headline {
            font-size: 18px;
            font-weight: 600;
            line-height: 1.4;
            margin-bottom: 12px;
            color: #F4F4F5;
        }
        .insight-summary {
            font-size: 14px;
            line-height: 1.6;
            color: #A1A1AA;
            margin-bottom: 16px;
        }
        .chart-container {
            margin: 16px 0;
            text-align: center;
        }
        .chart-image {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }
        .evidence {
            font-size: 12px;
            color: #71717A;
            margin-top: 12px;
        }
        .view-button {
            display: inline-block;
            background-color: #FF5A21;
            color: #FFFFFF;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            margin-top: 12px;
        }
        .footer {
            text-align: center;
            padding: 32px 0;
            border-top: 1px solid #2A2A2E;
            font-size: 12px;
            color: #71717A;
        }
        .footer-links {
            margin-top: 16px;
        }
        .footer-link {
            color: #A1A1AA;
            text-decoration: none;
            margin: 0 8px;
        }
        .footer-link:hover {
            color: #FF5A21;
        }
        @media only screen and (max-width: 600px) {
            .container {
                padding: 12px;
            }
            .insight-card {
                padding: 16px;
            }
            .insight-headline {
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">utxoIQ</div>
            <div class="subtitle">Bitcoin Blockchain Intelligence</div>
        </div>
        
        <div class="content">
            <div class="date-header">Daily Brief — {{ date }}</div>
            
            {% if summary %}
            <p style="font-size: 14px; line-height: 1.6; color: #A1A1AA; margin-bottom: 24px;">
                {{ summary }}
            </p>
            {% endif %}
            
            {% for insight in insights %}
            <div class="insight-card">
                <div class="insight-header">
                    <div class="signal-dot {{ insight.signal_type }}"></div>
                    <span class="signal-type">{{ insight.signal_type }}</span>
                    <span class="confidence-badge {% if insight.confidence >= 0.85 %}confidence-high{% else %}confidence-medium{% endif %}">
                        {{ (insight.confidence * 100)|int }}% confidence
                    </span>
                </div>
                
                <h2 class="insight-headline">{{ insight.headline }}</h2>
                <p class="insight-summary">{{ insight.summary }}</p>
                
                {% if insight.chart_url %}
                <div class="chart-container">
                    <img src="{{ insight.chart_url }}" alt="Chart" class="chart-image">
                </div>
                {% endif %}
                
                <div class="evidence">
                    Block {{ insight.block_height }}
                    {% if insight.evidence %}
                    • {{ insight.evidence|length }} citation(s)
                    {% endif %}
                </div>
                
                <a href="{{ frontend_url }}/insight/{{ insight.id }}" class="view-button">View Full Details</a>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>You're receiving this because you subscribed to utxoIQ Daily Briefs.</p>
            <div class="footer-links">
                <a href="{{ frontend_url }}/email/preferences?user_id={{ user_id }}" class="footer-link">Manage Preferences</a>
                <a href="{{ frontend_url }}/email/unsubscribe?user_id={{ user_id }}" class="footer-link">Unsubscribe</a>
                <a href="{{ frontend_url }}" class="footer-link">Visit utxoIQ</a>
            </div>
            <p style="margin-top: 16px;">© {{ year }} utxoIQ. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = self.env.from_string(template_str)
        return template.render(
            date=brief.date,
            summary=brief.summary,
            insights=brief.insights,
            user_id=user_id,
            frontend_url=settings.frontend_url,
            year=datetime.utcnow().year
        )
    
    def render_plain_text(self, brief: DailyBrief, user_id: str) -> str:
        """Render plain text version of daily brief."""
        lines = [
            "utxoIQ Daily Brief",
            "=" * 50,
            f"Date: {brief.date}",
            ""
        ]
        
        if brief.summary:
            lines.append(brief.summary)
            lines.append("")
        
        for i, insight in enumerate(brief.insights, 1):
            lines.extend([
                f"{i}. {insight.headline}",
                f"   Signal: {insight.signal_type.upper()}",
                f"   Confidence: {int(insight.confidence * 100)}%",
                f"   Block: {insight.block_height}",
                "",
                f"   {insight.summary}",
                "",
                f"   View details: {settings.frontend_url}/insight/{insight.id}",
                ""
            ])
        
        lines.extend([
            "=" * 50,
            f"Manage preferences: {settings.frontend_url}/email/preferences?user_id={user_id}",
            f"Unsubscribe: {settings.frontend_url}/email/unsubscribe?user_id={user_id}",
            "",
            f"© {datetime.utcnow().year} utxoIQ. All rights reserved."
        ])
        
        return "\n".join(lines)
