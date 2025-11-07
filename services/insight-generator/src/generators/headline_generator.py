"""
Headline generation with 280-character limit for X posts
Ensures headlines are concise and impactful
"""

import re
from typing import Optional


class HeadlineGenerator:
    """Generates and validates headlines for insights"""
    
    MAX_LENGTH = 280  # X (Twitter) character limit
    MIN_LENGTH = 20
    
    @staticmethod
    def validate_headline(headline: str) -> bool:
        """Validate headline meets requirements"""
        if not headline:
            return False
        
        # Check length
        if len(headline) < HeadlineGenerator.MIN_LENGTH:
            return False
        
        if len(headline) > HeadlineGenerator.MAX_LENGTH:
            return False
        
        # Check for basic content
        if not any(c.isalnum() for c in headline):
            return False
        
        return True
    
    @staticmethod
    def truncate_headline(headline: str, max_length: int = MAX_LENGTH) -> str:
        """Truncate headline to max length while preserving meaning"""
        if len(headline) <= max_length:
            return headline
        
        # Try to truncate at sentence boundary
        truncated = headline[:max_length - 3]
        
        # Find last sentence boundary
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        boundary = max(last_period, last_exclamation, last_question)
        
        if boundary > max_length // 2:  # Only use boundary if it's not too early
            return truncated[:boundary + 1]
        
        # Otherwise, truncate at word boundary
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + '...'
        
        return truncated + '...'
    
    @staticmethod
    def clean_headline(headline: str) -> str:
        """Clean and normalize headline text"""
        # Remove extra whitespace
        headline = re.sub(r'\s+', ' ', headline)
        headline = headline.strip()
        
        # Remove quotes if they wrap the entire headline
        if headline.startswith('"') and headline.endswith('"'):
            headline = headline[1:-1]
        if headline.startswith("'") and headline.endswith("'"):
            headline = headline[1:-1]
        
        # Ensure proper capitalization of first letter
        if headline and headline[0].islower():
            headline = headline[0].upper() + headline[1:]
        
        return headline
    
    @staticmethod
    def extract_headline_from_response(response_text: str) -> Optional[str]:
        """Extract headline from AI response"""
        # Try to find headline in JSON response
        import json
        try:
            data = json.loads(response_text)
            if 'headline' in data:
                return data['headline']
        except json.JSONDecodeError:
            pass
        
        # Try to find headline in markdown format
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            if line.startswith('Headline:'):
                return line.replace('Headline:', '').strip()
        
        # Return first non-empty line as fallback
        for line in lines:
            line = line.strip()
            if line and len(line) >= HeadlineGenerator.MIN_LENGTH:
                return line
        
        return None
    
    @staticmethod
    def format_for_x_post(headline: str, include_hashtags: bool = True) -> str:
        """Format headline for X (Twitter) post"""
        # Clean and truncate
        headline = HeadlineGenerator.clean_headline(headline)
        
        # Reserve space for hashtags if needed
        if include_hashtags:
            # Reserve ~30 characters for hashtags
            max_headline_length = HeadlineGenerator.MAX_LENGTH - 30
            headline = HeadlineGenerator.truncate_headline(headline, max_headline_length)
            
            # Add relevant hashtags
            hashtags = "\n\n#Bitcoin #BTC #Blockchain"
            return headline + hashtags
        else:
            headline = HeadlineGenerator.truncate_headline(headline)
            return headline
    
    @staticmethod
    def generate_fallback_headline(signal_type: str, block_height: int) -> str:
        """Generate a fallback headline if AI generation fails"""
        templates = {
            'mempool': f"Bitcoin mempool activity detected at block {block_height}",
            'exchange': f"Exchange flow anomaly detected at block {block_height}",
            'miner': f"Miner treasury movement detected at block {block_height}",
            'whale': f"Whale accumulation pattern detected at block {block_height}",
            'predictive': f"Predictive signal generated for upcoming blocks",
        }
        
        return templates.get(signal_type, f"Blockchain signal detected at block {block_height}")
    
    @staticmethod
    def enhance_headline_with_metrics(headline: str, key_metric: str, value: str) -> str:
        """Enhance headline with a key metric if space allows"""
        enhanced = f"{headline} ({key_metric}: {value})"
        
        if len(enhanced) <= HeadlineGenerator.MAX_LENGTH:
            return enhanced
        
        return headline
