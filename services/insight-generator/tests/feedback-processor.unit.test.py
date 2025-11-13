"""
Unit tests for feedback processing
"""

import pytest
from datetime import datetime, timedelta
from src.feedback.feedback_processor import (
    FeedbackProcessor,
    UserFeedback,
    FeedbackRating,
    AccuracyRating,
    ModelAccuracy
)


class TestFeedbackProcessor:
    """Test feedback processing functionality"""
    
    def test_store_feedback(self):
        """Test feedback storage"""
        processor = FeedbackProcessor()  # No BigQuery client for testing
        
        feedback = UserFeedback(
            insight_id='insight-123',
            user_id='user-456',
            rating=FeedbackRating.USEFUL,
            timestamp=datetime.now(),
            comment='Great insight!'
        )
        
        success = processor.store_feedback(feedback)
        
        assert success is True
    
    def test_calculate_accuracy_rating(self):
        """Test accuracy rating calculation"""
        processor = FeedbackProcessor()  # Mock mode
        
        rating = processor.calculate_accuracy_rating('insight-123')
        
        assert rating is not None
        assert rating.insight_id == 'insight-123'
        assert rating.total_feedback > 0
        assert 0.0 <= rating.accuracy_score <= 1.0
        assert rating.useful_count + rating.not_useful_count == rating.total_feedback
    
    def test_get_model_accuracy(self):
        """Test model accuracy calculation"""
        processor = FeedbackProcessor()  # Mock mode
        
        accuracy = processor.get_model_accuracy('1.0.0', 'mempool', days=30)
        
        assert accuracy is not None
        assert accuracy.model_version == '1.0.0'
        assert accuracy.signal_type == 'mempool'
        assert accuracy.total_insights > 0
        assert 0.0 <= accuracy.accuracy_score <= 1.0
    
    def test_get_model_accuracy_all_signals(self):
        """Test model accuracy for all signal types"""
        processor = FeedbackProcessor()  # Mock mode
        
        accuracy = processor.get_model_accuracy('1.0.0', signal_type=None, days=30)
        
        assert accuracy is not None
        assert accuracy.signal_type == 'all'
    
    def test_get_accuracy_leaderboard(self):
        """Test accuracy leaderboard retrieval"""
        processor = FeedbackProcessor()  # Mock mode
        
        leaderboard = processor.get_accuracy_leaderboard(limit=10, days=30)
        
        assert isinstance(leaderboard, list)
        assert len(leaderboard) > 0
        
        # Check sorting (highest accuracy first)
        if len(leaderboard) > 1:
            assert leaderboard[0].accuracy_score >= leaderboard[1].accuracy_score
    
    def test_collect_retraining_data(self):
        """Test retraining data collection"""
        processor = FeedbackProcessor()  # Mock mode
        
        data = processor.collect_retraining_data(
            signal_type='mempool',
            min_feedback=5,
            days=90
        )
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check data structure
        if data:
            item = data[0]
            assert 'insight_id' in item
            assert 'signal_type' in item
            assert 'confidence' in item
            assert 'accuracy_score' in item
    
    def test_user_feedback_to_dict(self):
        """Test UserFeedback serialization"""
        feedback = UserFeedback(
            insight_id='insight-123',
            user_id='user-456',
            rating=FeedbackRating.USEFUL,
            timestamp=datetime.now(),
            comment='Test comment'
        )
        
        feedback_dict = feedback.to_dict()
        
        assert feedback_dict['insight_id'] == 'insight-123'
        assert feedback_dict['user_id'] == 'user-456'
        assert feedback_dict['rating'] == 'useful'
        assert feedback_dict['comment'] == 'Test comment'
    
    def test_accuracy_rating_to_dict(self):
        """Test AccuracyRating serialization"""
        rating = AccuracyRating(
            insight_id='insight-123',
            total_feedback=10,
            useful_count=8,
            not_useful_count=2,
            accuracy_score=0.8
        )
        
        rating_dict = rating.to_dict()
        
        assert rating_dict['insight_id'] == 'insight-123'
        assert rating_dict['total_feedback'] == 10
        assert rating_dict['useful_count'] == 8
        assert rating_dict['accuracy_score'] == 0.8
    
    def test_model_accuracy_to_dict(self):
        """Test ModelAccuracy serialization"""
        now = datetime.now()
        past = now - timedelta(days=30)
        
        accuracy = ModelAccuracy(
            model_version='1.0.0',
            signal_type='mempool',
            total_insights=100,
            total_feedback=75,
            accuracy_score=0.82,
            period_start=past,
            period_end=now
        )
        
        accuracy_dict = accuracy.to_dict()
        
        assert accuracy_dict['model_version'] == '1.0.0'
        assert accuracy_dict['signal_type'] == 'mempool'
        assert accuracy_dict['total_insights'] == 100
        assert accuracy_dict['accuracy_score'] == 0.82
