"""Enhanced Tally ledger matching with improved accuracy."""

from typing import List, Tuple, Optional, Dict
from thefuzz import fuzz
from engine.utils.normalizers import normalize_name, normalize_party_name


class TallyLedgerMatcher:
    """
    Match extracted bank names to existing Tally ledgers.
    """
    
    def __init__(self, tally_ledger_names: List[str], 
                 fuzzy_threshold: int = 80,
                 exact_match_priority: bool = True):
        """
        Initialize matcher.
        
        Args:
            tally_ledger_names: List of existing Tally ledger names
            fuzzy_threshold: Threshold for fuzzy matching (0-100)
            exact_match_priority: Prioritize exact matches
        """
        self.tally_ledgers = tally_ledger_names
        self.fuzzy_threshold = fuzzy_threshold
        self.exact_match_priority = exact_match_priority
        self.normalized_ledgers = {
            normalize_party_name(name): name for name in tally_ledger_names
        }
    
    def find_best_match(self, extracted_name: str) -> Tuple[Optional[str], int]:
        """
        Find best matching Tally ledger for extracted name.
        
        Args:
            extracted_name: Name extracted from bank statement
            
        Returns:
            Tuple of (ledger_name, confidence_score)
        """
        if not extracted_name or not self.tally_ledgers:
            return None, 0
        
        extracted_upper = str(extracted_name).upper().strip()
        extracted_norm = normalize_party_name(extracted_name)
        
        # 1. Exact match (highest priority)
        for ledger in self.tally_ledgers:
            if ledger.upper().strip() == extracted_upper:
                return ledger, 100
        
        # 2. Normalized match
        if extracted_norm in self.normalized_ledgers:
            return self.normalized_ledgers[extracted_norm], 95
        
        # 3. Fuzzy matching
        best_match = None
        best_score = 0
        
        for ledger in self.tally_ledgers:
            # Try multiple similarity metrics
            scores = [
                fuzz.ratio(extracted_upper, ledger.upper()),
                fuzz.partial_ratio(extracted_upper, ledger.upper()),
                fuzz.token_sort_ratio(extracted_norm, normalize_party_name(ledger)),
            ]
            
            max_score = max(scores)
            
            if max_score > best_score:
                best_score = max_score
                best_match = ledger
        
        # Return match if above threshold
        if best_score >= self.fuzzy_threshold:
            return best_match, best_score
        
        return None, best_score
    
    def find_all_candidates(self, extracted_name: str, threshold: int = 70) -> List[Tuple[str, int]]:
        """
        Find all potential Tally ledgers above threshold.
        
        Args:
            extracted_name: Name to search for
            threshold: Minimum match score
            
        Returns:
            List of (ledger_name, score) tuples sorted by score descending
        """
        candidates = []
        extracted_upper = extracted_name.upper().strip()
        
        for ledger in self.tally_ledgers:
            score = fuzz.token_sort_ratio(extracted_upper, ledger.upper())
            if score >= threshold:
                candidates.append((ledger, score))
        
        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates
