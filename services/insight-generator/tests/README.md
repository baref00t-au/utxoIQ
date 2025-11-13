# insight-generator Tests

## Test Files

- `confidence-scorer.unit.test.py` - Confidence scoring algorithm tests
- `explainability-generator.unit.test.py` - Insight explainability tests
- `feedback-processor.unit.test.py` - User feedback processing tests
- `insight-generator.integration.test.py` - Full insight generation pipeline tests
- `prompt-templates.unit.test.py` - AI prompt template tests

## Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/insight-generator.integration.test.py

# Run with coverage
pytest --cov=src tests/
```
