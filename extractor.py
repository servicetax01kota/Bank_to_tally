# engine/extractor.py
"""
Main extraction orchestrator.
Uses parser_manager to delegate to bank-specific parsers.
"""

from engine.parser_manager import get_parser_manager


def extract_account_info(narration, bank_id):
    """
    Extracts party name and transaction type from bank narration.
    
    Args:
        narration (str): Bank statement narration/description text
        bank_id (str): Bank identifier from parser configuration
        
    Returns:
        dict: {
            'extracted_name': str or None,
            'type': 'Payment' or 'Receipt',
            'needs_review': bool
        }
    """
    n = str(narration).strip()
    upper_n = n.upper()
    
    result = {
        'extracted_name': None,
        'type': 'Payment',  # Default
        'needs_review': False
    }
    
    # ============================================
    # KEYWORD CLASSIFICATION (Bank-wide)
    # These apply regardless of bank
    # ============================================
    
    # Cash related
    if any(keyword in upper_n for keyword in ['CASH DEPOSIT', 'CASH CHEQUE', 'CASH WDL', 'CASH WITHDRAWAL']):
        result['extracted_name'] = 'Cash'
        return result
    
    # Bank charges / ATM fees
    if any(keyword in upper_n for keyword in ['ATMCARD', 'ATM CARD', 'AMC ', 'CHARGES', 'CHG ', 'FEE']):
        result['extracted_name'] = 'Bank Charges'
        return result
    
    # ============================================
    # BANK-SPECIFIC EXTRACTION
    # ============================================
    
    parser_manager = get_parser_manager()
    extract_func = parser_manager.get_extract_function(bank_id)
    
    if extract_func:
        extracted = extract_func(n)
        if extracted:
            result['extracted_name'] = extracted
        else:
            # No name extracted - mark for review
            result['needs_review'] = True
    else:
        result['needs_review'] = True
    
    return result