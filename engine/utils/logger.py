"""Centralized logging for audit trail."""

import logging
import os
from datetime import datetime
import json


class AuditLogger:
    """
    Centralized audit logging for all operations.
    """
    
    def __init__(self, log_file: str = "bank_to_tally.log"):
        """
        Initialize audit logger.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        self.audit_events = []
        
        # Setup standard logging
        self.logger = logging.getLogger('BankToTally')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        try:
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        except Exception as e:
            print(f"Warning: Could not create log file: {e}")
    
    def log_event(self, event_type: str, details: dict):
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., 'DUPLICATE_SKIPPED', 'LEDGER_CREATED')
            details: Event details dictionary
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        self.audit_events.append(event)
        self.logger.info(f"{event_type}: {json.dumps(details)}")
    
    def log_processing_start(self, bank_name: str, statement_file: str):
        """
        Log start of processing.
        
        Args:
            bank_name: Bank name
            statement_file: Statement file path
        """
        self.log_event('PROCESSING_START', {
            'bank_name': bank_name,
            'file': os.path.basename(statement_file)
        })
    
    def log_duplicate_skipped(self, transaction: dict, reason: str):
        """
        Log skipped duplicate.
        
        Args:
            transaction: Transaction data
            reason: Skip reason
        """
        self.log_event('DUPLICATE_SKIPPED', {
            'date': transaction.get('date'),
            'party': transaction.get('mapped_ledger'),
            'amount': transaction.get('amount'),
            'reason': reason
        })
    
    def log_ledger_created(self, ledger_name: str, group: str):
        """
        Log new ledger creation.
        
        Args:
            ledger_name: Ledger name
            group: Parent group
        """
        self.log_event('LEDGER_CREATED', {
            'name': ledger_name,
            'group': group
        })
    
    def log_ledger_skipped(self, ledger_name: str, reason: str):
        """
        Log skipped ledger (already exists).
        
        Args:
            ledger_name: Ledger name
            reason: Skip reason
        """
        self.log_event('LEDGER_SKIPPED', {
            'name': ledger_name,
            'reason': reason
        })
    
    def log_mapping(self, extracted_name: str, tally_ledger: str, confidence: float):
        """
        Log name mapping.
        
        Args:
            extracted_name: Extracted bank name
            tally_ledger: Mapped Tally ledger
            confidence: Confidence score (0-100)
        """
        self.log_event('NAME_MAPPING', {
            'extracted': extracted_name,
            'mapped_to': tally_ledger,
            'confidence': confidence
        })
    
    def get_report(self) -> dict:
        """
        Get processing report.
        
        Returns:
            Dictionary with event summary
        """
        event_counts = {}
        for event in self.audit_events:
            event_type = event['event_type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'total_events': len(self.audit_events),
            'event_counts': event_counts,
            'events': self.audit_events
        }
