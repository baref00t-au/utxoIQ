"""Chat resource for utxoIQ API."""
from ..models import ChatResponse


class ChatResource:
    """Resource for AI chat queries."""
    
    def __init__(self, client):
        self.client = client
    
    def query(self, question: str) -> ChatResponse:
        """
        Ask a natural language question about Bitcoin blockchain data.
        
        Args:
            question: Natural language question
        
        Returns:
            ChatResponse object with answer and citations
        """
        payload = {"question": question}
        response = self.client.post("/chat/query", json=payload)
        return ChatResponse(**response.json())
