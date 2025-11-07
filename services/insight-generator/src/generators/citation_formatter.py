"""
Evidence citation formatting and validation
Creates blockchain evidence citations for insights
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field, validator


class Citation(BaseModel):
    """Citation model for blockchain evidence"""
    type: str = Field(..., pattern="^(block|transaction|address)$")
    id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)

    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class CitationFormatter:
    """Formats blockchain evidence into citations"""
    
    # Base URLs for blockchain explorers
    BLOCK_EXPLORER_BASE = "https://mempool.space"
    
    @staticmethod
    def create_block_citation(block_height: int, description: str = None) -> Citation:
        """Create a citation for a block"""
        if description is None:
            description = f"Block #{block_height}"
        
        return Citation(
            type="block",
            id=str(block_height),
            description=description,
            url=f"{CitationFormatter.BLOCK_EXPLORER_BASE}/block/{block_height}"
        )
    
    @staticmethod
    def create_transaction_citation(tx_hash: str, description: str = None) -> Citation:
        """Create a citation for a transaction"""
        if description is None:
            description = f"Transaction {tx_hash[:8]}..."
        
        return Citation(
            type="transaction",
            id=tx_hash,
            description=description,
            url=f"{CitationFormatter.BLOCK_EXPLORER_BASE}/tx/{tx_hash}"
        )
    
    @staticmethod
    def create_address_citation(address: str, description: str = None) -> Citation:
        """Create a citation for an address"""
        if description is None:
            description = f"Address {address[:8]}..."
        
        return Citation(
            type="address",
            id=address,
            description=description,
            url=f"{CitationFormatter.BLOCK_EXPLORER_BASE}/address/{address}"
        )
    
    @staticmethod
    def create_citations_from_signal(signal_data: Dict[str, Any]) -> List[Citation]:
        """Create citations from signal data"""
        citations = []
        
        # Add block citation
        if 'block_height' in signal_data:
            citations.append(
                CitationFormatter.create_block_citation(
                    signal_data['block_height'],
                    f"Block #{signal_data['block_height']} - Signal detected"
                )
            )
        
        # Add transaction citations
        if 'transaction_ids' in signal_data:
            tx_ids = signal_data['transaction_ids']
            if tx_ids:
                # Limit to first 3 transactions to avoid clutter
                for tx_id in tx_ids[:3]:
                    citations.append(
                        CitationFormatter.create_transaction_citation(
                            tx_id,
                            f"Related transaction"
                        )
                    )
                
                # Add summary if more transactions exist
                if len(tx_ids) > 3:
                    citations.append(
                        Citation(
                            type="transaction",
                            id="summary",
                            description=f"Plus {len(tx_ids) - 3} more transactions",
                            url=f"{CitationFormatter.BLOCK_EXPLORER_BASE}/block/{signal_data['block_height']}"
                        )
                    )
        
        # Add address citations for entity-based signals
        if 'entity_ids' in signal_data and 'addresses' in signal_data:
            addresses = signal_data['addresses']
            if addresses:
                # Limit to first 2 addresses
                for address in addresses[:2]:
                    entity_name = signal_data.get('entity_name', 'Unknown entity')
                    citations.append(
                        CitationFormatter.create_address_citation(
                            address,
                            f"{entity_name} address"
                        )
                    )
        
        return citations
    
    @staticmethod
    def validate_citations(citations: List[Citation]) -> bool:
        """Validate a list of citations"""
        if not citations:
            return False
        
        # Ensure at least one citation exists
        if len(citations) < 1:
            return False
        
        # Validate each citation
        for citation in citations:
            try:
                # Pydantic validation happens automatically
                if not citation.id or not citation.description or not citation.url:
                    return False
            except Exception:
                return False
        
        return True
    
    @staticmethod
    def format_citations_for_display(citations: List[Citation]) -> str:
        """Format citations for human-readable display"""
        if not citations:
            return "No evidence citations available"
        
        formatted = []
        for citation in citations:
            formatted.append(f"• {citation.description}: {citation.url}")
        
        return "\n".join(formatted)
