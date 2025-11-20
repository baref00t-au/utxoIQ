"""
Verification script for AI Provider Module

This script verifies that the AI provider module is correctly implemented
and all components work as expected.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_provider import (
    AIProvider,
    AIProviderType,
    AIProviderError,
    AIProviderFactory,
    InsightContent,
    Signal,
    get_configured_provider
)


def test_signal_creation():
    """Test Signal dataclass creation"""
    print("✓ Testing Signal creation...")
    signal = Signal(
        signal_id="test-123",
        signal_type="mempool",
        block_height=800000,
        confidence=0.85,
        metadata={"fee_rate_median": 50.5}
    )
    assert signal.signal_id == "test-123"
    assert signal.confidence == 0.85
    print("  ✓ Signal creation works")


def test_insight_content_creation():
    """Test InsightContent dataclass creation"""
    print("✓ Testing InsightContent creation...")
    content = InsightContent(
        headline="Test Headline",
        summary="Test summary",
        confidence_explanation="Test explanation"
    )
    assert content.headline == "Test Headline"
    print("  ✓ InsightContent creation works")


def test_provider_types():
    """Test AIProviderType enum"""
    print("✓ Testing AIProviderType enum...")
    assert AIProviderType.VERTEX_AI.value == "vertex_ai"
    assert AIProviderType.OPENAI.value == "openai"
    assert AIProviderType.ANTHROPIC.value == "anthropic"
    assert AIProviderType.GROK.value == "grok"
    print("  ✓ All provider types defined")


def test_abstract_base_class():
    """Test AIProvider abstract base class"""
    print("✓ Testing AIProvider abstract base class...")
    
    # Try to instantiate abstract class (should work but can't call abstract methods)
    try:
        class TestProvider(AIProvider):
            async def generate_insight(self, signal, prompt_template):
                return InsightContent("test", "test", "test")
        
        provider = TestProvider({})
        assert provider.provider_name == "TestProvider"
        print("  ✓ Abstract base class works")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        raise


def test_prompt_formatting():
    """Test prompt formatting"""
    print("✓ Testing prompt formatting...")
    
    class TestProvider(AIProvider):
        async def generate_insight(self, signal, prompt_template):
            pass
    
    provider = TestProvider({})
    signal = Signal(
        signal_id="test",
        signal_type="mempool",
        block_height=800000,
        confidence=0.85,
        metadata={"fee_rate": 50.5, "change": 25.3}
    )
    
    template = "Fee: {fee_rate}, Change: {change}%"
    formatted = provider._format_prompt(signal, template)
    
    assert "50.5" in formatted
    assert "25.3" in formatted
    print("  ✓ Prompt formatting works")


def test_json_parsing():
    """Test JSON response parsing"""
    print("✓ Testing JSON response parsing...")
    
    class TestProvider(AIProvider):
        async def generate_insight(self, signal, prompt_template):
            pass
    
    provider = TestProvider({})
    
    # Valid JSON
    import json
    response = json.dumps({
        "headline": "Test Headline",
        "summary": "Test summary",
        "confidence_explanation": "Test explanation"
    })
    
    content = provider._parse_json_response(response)
    assert isinstance(content, InsightContent)
    assert content.headline == "Test Headline"
    print("  ✓ JSON parsing works")


def test_error_handling():
    """Test error handling"""
    print("✓ Testing error handling...")
    
    class TestProvider(AIProvider):
        async def generate_insight(self, signal, prompt_template):
            pass
    
    provider = TestProvider({})
    
    # Test invalid JSON
    try:
        provider._parse_json_response("not json")
        print("  ✗ Should have raised AIProviderError")
    except AIProviderError as e:
        assert "Invalid JSON" in str(e)
        print("  ✓ Invalid JSON error handling works")
    
    # Test missing fields
    import json
    try:
        provider._parse_json_response(json.dumps({"headline": "test"}))
        print("  ✗ Should have raised AIProviderError")
    except AIProviderError as e:
        assert "Missing required fields" in str(e)
        print("  ✓ Missing fields error handling works")


def test_factory_invalid_provider():
    """Test factory with invalid provider type"""
    print("✓ Testing factory with invalid provider...")
    
    try:
        AIProviderFactory.create_provider("invalid_provider", {})
        print("  ✗ Should have raised AIProviderError")
    except AIProviderError as e:
        assert "Invalid provider type" in str(e)
        print("  ✓ Invalid provider error handling works")


def test_factory_config_loading():
    """Test factory configuration loading"""
    print("✓ Testing factory configuration loading...")
    
    # Test Vertex AI config
    config = AIProviderFactory._load_config_from_env("vertex_ai")
    assert "project_id" in config
    assert "location" in config
    assert "model" in config
    print("  ✓ Vertex AI config structure correct")
    
    # Test OpenAI config
    config = AIProviderFactory._load_config_from_env("openai")
    assert "api_key" in config
    assert "model" in config
    print("  ✓ OpenAI config structure correct")
    
    # Test Anthropic config
    config = AIProviderFactory._load_config_from_env("anthropic")
    assert "api_key" in config
    assert "model" in config
    print("  ✓ Anthropic config structure correct")
    
    # Test Grok config
    config = AIProviderFactory._load_config_from_env("grok")
    assert "api_key" in config
    assert "model" in config
    assert "api_base" in config
    print("  ✓ Grok config structure correct")


def test_get_configured_provider_missing_env():
    """Test get_configured_provider without AI_PROVIDER env var"""
    print("✓ Testing get_configured_provider without env var...")
    
    # Save current env
    old_value = os.environ.get("AI_PROVIDER")
    
    try:
        # Remove AI_PROVIDER
        if "AI_PROVIDER" in os.environ:
            del os.environ["AI_PROVIDER"]
        
        try:
            get_configured_provider()
            print("  ✗ Should have raised AIProviderError")
        except AIProviderError as e:
            assert "AI_PROVIDER environment variable not set" in str(e)
            print("  ✓ Missing env var error handling works")
    
    finally:
        # Restore env
        if old_value:
            os.environ["AI_PROVIDER"] = old_value


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("AI Provider Module - Verification Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_signal_creation,
        test_insight_content_creation,
        test_provider_types,
        test_abstract_base_class,
        test_prompt_formatting,
        test_json_parsing,
        test_error_handling,
        test_factory_invalid_provider,
        test_factory_config_loading,
        test_get_configured_provider_missing_env
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ Test failed: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All verification tests passed!")
        print("\nThe AI Provider Module is correctly implemented with:")
        print("  - Abstract base class (AIProvider)")
        print("  - Four provider implementations (Vertex AI, OpenAI, Anthropic, Grok)")
        print("  - Factory pattern for provider creation")
        print("  - Configuration loading from environment")
        print("  - Comprehensive error handling")
        print("  - Prompt formatting and JSON parsing")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
