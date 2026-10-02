"""
PetroNexus Ingestion Adapter Interface (SIH 26121 Section 4)
Standardized base class for all real and public data source connectors.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

class DataSourceAdapter(ABC):

    def __init__(self, source_name: str, source_type: str):
        self.source_name = source_name
        self.source_type = source_type
        self.status = "STANDBY" # CONNECTED, CONNECTING, DISCONNECTED, ERROR, STANDBY
        self.last_update = None
        self.error_message = None

    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """Establishes connection or initializes resource"""
        pass

    @abstractmethod
    def validate(self, source_data: Any) -> Dict[str, Any]:
        """Validates schema, required fields, and physical feasibility"""
        pass

    @abstractmethod
    def discover(self, source_data: Any) -> Dict[str, Any]:
        """Discovers available channels, columns, formations or curve mnemonics"""
        pass

    @abstractmethod
    def ingest(self, source_data: Any, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts and normalizes raw dataset into PetroNexus canonical entities"""
        pass

    @abstractmethod
    def normalize(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts units and cleans timestamps and values"""
        pass

    @abstractmethod
    def store(self, db: Session, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Persists records into relational database tables with provenance tracking"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Returns standard health and connectivity metrics"""
        return {
            "source_name": self.source_name,
            "source_type": self.source_type,
            "status": self.status,
            "last_update": self.last_update,
            "error_message": self.error_message
        }
