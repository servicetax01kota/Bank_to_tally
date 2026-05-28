"""Fast duplicate checking using indexing for O(1) lookups."""

from typing import List, Dict, Optional
from engine.tally_parser import TallyVoucher
from engine.utils.normalizers import normalize_date_for_comparison, normalize_amount, normalize_party_name
import json


class DuplicateIndex:
    """
    Efficient duplicate checking using indexed lookups.
    """
    
    def __init__(self, daybook_vouchers: List[TallyVoucher], 
                 date_tolerance_days: int = 3,
                 amount_tolerance: float = 0.02):
        """
        Initialize duplicate index.
        
        Args:
            daybook_vouchers: List of existing Tally vouchers
            date_tolerance_days: Days to tolerate in date differences
            amount_tolerance: Amount tolerance for fuzzy matching
        """
        self.date_tolerance = date_tolerance_days
        self.amount_tolerance = amount_tolerance
        self.index = {}  # key -> list of vouchers
        self.vouchers = daybook_vouchers
        self._build_index()
    
    def _build_index(self):
        """
        Build index for fast lookups.
        """
        for voucher in self.vouchers:
            # Create composite key: party name is most important
            party_norm = normalize_party_name(voucher.party_name)
            
            if party_norm not in self.index:
                self.index[party_norm] = []
            
            self.index[party_norm].append(voucher)
    
    def find_duplicates(self, trans_date: str, amount: float, party_name: str) -> List[TallyVoucher]:
        """
        Find duplicate vouchers for a transaction.
        
        Args:
            trans_date: Transaction date
            amount: Transaction amount
            party_name: Party/ledger name
            
        Returns:
            List of matching vouchers
        """
        party_norm = normalize_party_name(party_name)
        
        # Quick check: if party not in index, no duplicates
        if party_norm not in self.index:
            return []
        
        candidates = self.index[party_norm]
        matches = []
        
        trans_date_norm = normalize_date_for_comparison(trans_date)
        trans_amount_norm = normalize_amount(amount)
        
        for voucher in candidates:
            # Check amount (within tolerance)
            voucher_amount = normalize_amount(voucher.amount)
            if abs(trans_amount_norm - voucher_amount) > self.amount_tolerance:
                continue
            
            # Check date (within tolerance)
            voucher_date_norm = normalize_date_for_comparison(voucher.date)
            
            if trans_date_norm and voucher_date_norm:
                try:
                    date_diff = abs(int(trans_date_norm) - int(voucher_date_norm))
                    if date_diff > self.date_tolerance:
                        continue
                except (ValueError, TypeError):
                    continue
            
            matches.append(voucher)
        
        return matches


def check_duplicate_in_daybook(
    transaction_date: str,
    amount: float,
    party_name: str,
    daybook_vouchers: List[TallyVoucher],
    date_tolerance_days: int = 3,
    amount_tolerance: float = 0.02
) -> List[TallyVoucher]:
    """
    Check if transaction already exists in Tally Day Book.
    
    Args:
        transaction_date: Transaction date
        amount: Transaction amount
        party_name: Party name
        daybook_vouchers: List of daybook vouchers to check against
        date_tolerance_days: Days tolerance
        amount_tolerance: Amount tolerance
        
    Returns:
        List of duplicate vouchers found
    """
    index = DuplicateIndex(daybook_vouchers, date_tolerance_days, amount_tolerance)
    return index.find_duplicates(transaction_date, amount, party_name)
