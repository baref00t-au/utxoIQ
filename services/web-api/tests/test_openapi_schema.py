"""OpenAPI schema validation tests."""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestOpenAPISchema:
    """Test OpenAPI schema generation and validation."""
    
    def test_openapi_json_endpoint(self):
        """Test that OpenAPI JSON schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        
        # Validate OpenAPI version
        assert "openapi" in schema
        assert schema["openapi"].startswith("3.")
        
        # Validate info section
        assert "info" in schema
        assert schema["info"]["title"] == "utxoIQ API"
        assert schema["info"]["version"] == "1.0.0"
        assert "description" in schema["info"]
        assert "contact" in schema["info"]
        assert "license" in schema["info"]
    
    def test_security_schemes_defined(self):
        """Test that security schemes are properly defined."""
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert "components" in schema
        assert "securitySchemes" in schema["components"]
        
        # Check FirebaseAuth scheme
        assert "FirebaseAuth" in schema["components"]["securitySchemes"]
        firebase_auth = schema["components"]["securitySchemes"]["FirebaseAuth"]
        assert firebase_auth["type"] == "http"
        assert firebase_auth["scheme"] == "bearer"
        assert firebase_auth["bearerFormat"] == "JWT"
        
        # Check ApiKeyAuth scheme
        assert "ApiKeyAuth" in schema["components"]["securitySchemes"]
        api_key_auth = schema["components"]["securitySchemes"]["ApiKeyAuth"]
        assert api_key_auth["type"] == "apiKey"
        assert api_key_auth["in"] == "header"
        assert api_key_auth["name"] == "X-API-Key"
    
    def test_paths_defined(self):
        """Test that API paths are defined in schema."""
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert "paths" in schema
        paths = schema["paths"]
        
        # Check key endpoints are present
        assert "/insights/latest" in paths
        assert "/insights/public" in paths
        assert "/insights/{insight_id}" in paths
        assert "/alerts" in paths
        assert "/chat/query" in paths
        assert "/billing/subscription" in paths
        assert "/daily-brief/{brief_date}" in paths
    
    def test_operation_ids_present(self):
        """Test that operation IDs are defined for SDK generation."""
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check that key operations have operation IDs
        insights_latest = schema["paths"]["/insights/latest"]["get"]
        assert "operationId" in insights_latest
        assert insights_latest["operationId"] == "getLatestInsights"
        
        insights_public = schema["paths"]["/insights/public"]["get"]
        assert "operationId" in insights_public
        assert insights_public["operationId"] == "getPublicInsights"
    
    def test_response_schemas_defined(self):
        """Test that response schemas are properly defined."""
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check that responses have proper schemas
        insights_latest = schema["paths"]["/insights/latest"]["get"]
        assert "responses" in insights_latest
        assert "200" in insights_latest["responses"]
        assert "429" in insights_latest["responses"]
        assert "500" in insights_latest["responses"]
    
    def test_tags_defined(self):
        """Test that API tags are defined for organization."""
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check that paths have tags
        insights_latest = schema["paths"]["/insights/latest"]["get"]
        assert "tags" in insights_latest
        assert "insights" in insights_latest["tags"]
    
    def test_swagger_ui_accessible(self):
        """Test that Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Check that it contains Swagger UI elements
        assert b"swagger" in response.content.lower()
    
    def test_redoc_ui_accessible(self):
        """Test that ReDoc UI is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Check that it contains ReDoc elements
        assert b"redoc" in response.content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
