"""Validation utilities for data integrity."""

from typing import List, Dict, Tuple


def validate_transactions(transactions: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Validate transaction data before XML generation.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Tuple of (valid_transactions, error_messages)
    """
    valid = []
    errors = []
    
    for idx, trans in enumerate(transactions):
        trans_errors = []
        
        # Validate date
        if not trans.get('date'):
            trans_errors.append(f"Missing date")
        
        # Validate amount
        try:
            amount = float(trans.get('amount', 0))
            if amount <= 0:
                trans_errors.append(f"Invalid amount: {amount}")
        except (ValueError, TypeError):
            trans_errors.append(f"Invalid amount format: {trans.get('amount')}")
        
        # Validate mapped ledger
        if not trans.get('mapped_ledger') or str(trans.get('mapped_ledger')).strip() == '':
            trans_errors.append(f"No ledger mapping")
        
        # Validate narration
        if not trans.get('narration'):
            trans_errors.append(f"Missing narration")
        
        if trans_errors:
            for error in trans_errors:
                errors.append(f"Row {idx}: {error}")
        else:
            valid.append(trans)
    
    return valid, errors


def is_valid_ledger_name(name: str) -> bool:
    """
    Check if ledger name is valid.
    
    Args:
        name: Ledger name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    
    name = str(name).strip()
    
    if name == '':
        return False
    
    invalid_names = {
        'UNKNOWN', 'UNKNOWN TRANSACTION', 'NONE', 'NULL', 'NAN',
        'PAYMENT MADE', 'PAYMENT RECEIPT', 'UNDEFINED', 'N/A'
    }
    
    return name.upper() not in invalid_names


def validate_ledger_for_tally(ledger_name: str, existing_ledger_names: List[str]) -> Dict:
    """
    Validate if ledger can be created in Tally (check for duplicates).
    
    Args:
        ledger_name: New ledger name to create
        existing_ledger_names: List of existing Tally ledger names
        
    Returns:
        Dict with 'valid', 'reason', and 'existing_match' keys
    """
    if not is_valid_ledger_name(ledger_name):
        return {'valid': False, 'reason': 'Invalid ledger name', 'existing_match': None}
    
    from engine.utils.normalizers import normalize_party_name
    
    new_normalized = normalize_party_name(ledger_name)
    
    # Check exact match
    for existing in existing_ledger_names:
        if existing.upper().strip() == ledger_name.upper().strip():
            return {'valid': False, 'reason': 'Exact duplicate exists', 'existing_match': existing}
    
    # Check normalized match
    for existing in existing_ledger_names:
        existing_normalized = normalize_party_name(existing)
        if existing_normalized == new_normalized:
            return {'valid': False, 'reason': 'Normalized duplicate exists', 'existing_match': existing}
    
    return {'valid': True, 'reason': 'Valid - can be created', 'existing_match': None}
