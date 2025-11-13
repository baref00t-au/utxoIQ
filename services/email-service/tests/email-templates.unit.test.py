"""Tests for email template rendering."""
import pytest
from src.email_templates import EmailTemplates


def test_render_daily_brief_html(sample_daily_brief):
    """Test rendering daily brief HTML template."""
    templates = EmailTemplates()
    
    html = templates.render_daily_brief(sample_daily_brief, "user_123")
    
    # Check key elements are present
    assert "utxoIQ" in html
    assert "Daily Brief" in html
    assert sample_daily_brief.date in html
    assert sample_daily_brief.insights[0].headline in html
    assert sample_daily_brief.insights[0].summary in html
    assert str(sample_daily_brief.insights[0].block_height) in html
    assert "85% confidence" in html  # 0.85 * 100
    assert "user_123" in html  # User ID in unsubscribe link


def test_render_daily_brief_with_chart(sample_daily_brief):
    """Test rendering daily brief with chart URL."""
    templates = EmailTemplates()
    
    html = templates.render_daily_brief(sample_daily_brief, "user_123")
    
    # Check chart image is included
    assert sample_daily_brief.insights[0].chart_url in html
    assert '<img' in html


def test_render_daily_brief_with_summary(sample_daily_brief):
    """Test rendering daily brief with summary."""
    templates = EmailTemplates()
    sample_daily_brief.summary = "Test summary text"
    
    html = templates.render_daily_brief(sample_daily_brief, "user_123")
    
    assert "Test summary text" in html


def test_render_daily_brief_without_summary(sample_daily_brief):
    """Test rendering daily brief without summary."""
    templates = EmailTemplates()
    sample_daily_brief.summary = None
    
    html = templates.render_daily_brief(sample_daily_brief, "user_123")
    
    # Should still render successfully
    assert "utxoIQ" in html
    assert sample_daily_brief.insights[0].headline in html


def test_render_plain_text(sample_daily_brief):
    """Test rendering plain text version."""
    templates = EmailTemplates()
    
    text = templates.render_plain_text(sample_daily_brief, "user_123")
    
    # Check key elements are present
    assert "utxoIQ Daily Brief" in text
    assert sample_daily_brief.date in text
    assert sample_daily_brief.insights[0].headline in text
    assert sample_daily_brief.insights[0].summary in text
    assert str(sample_daily_brief.insights[0].block_height) in text
    assert "85%" in text
    assert "user_123" in text


def test_render_multiple_insights(sample_insight):
    """Test rendering brief with multiple insights."""
    templates = EmailTemplates()
    
    # Create brief with multiple insights
    insight2 = sample_insight.model_copy()
    insight2.id = "insight_456"
    insight2.headline = "Second insight headline"
    insight2.signal_type = "exchange"
    
    brief = type('DailyBrief', (), {
        'date': '2025-11-06',
        'insights': [sample_insight, insight2],
        'summary': None
    })()
    
    html = templates.render_daily_brief(brief, "user_123")
    
    # Both insights should be present
    assert sample_insight.headline in html
    assert insight2.headline in html


def test_confidence_badge_colors(sample_insight):
    """Test confidence badge color classes."""
    templates = EmailTemplates()
    
    # High confidence (>= 0.85)
    sample_insight.confidence = 0.90
    brief = type('DailyBrief', (), {
        'date': '2025-11-06',
        'insights': [sample_insight],
        'summary': None
    })()
    
    html = templates.render_daily_brief(brief, "user_123")
    assert "confidence-high" in html
    
    # Medium confidence (< 0.85)
    sample_insight.confidence = 0.75
    html = templates.render_daily_brief(brief, "user_123")
    assert "confidence-medium" in html


def test_signal_type_styling(sample_insight):
    """Test signal type dot colors."""
    templates = EmailTemplates()
    
    signal_types = ["mempool", "exchange", "miner", "whale"]
    
    for signal_type in signal_types:
        sample_insight.signal_type = signal_type
        brief = type('DailyBrief', (), {
            'date': '2025-11-06',
            'insights': [sample_insight],
            'summary': None
        })()
        
        html = templates.render_daily_brief(brief, "user_123")
        assert f'signal-dot {signal_type}' in html
