# engine/matcher.py
"""
Fuzzy matching for grouping similar account names.
Uses multiple algorithms for better matching with higher precision.
"""

from thefuzz import fuzz, process
from typing import List, Dict, Tuple, Optional
import re


def normalize_name(name: str) -> str:
    """
    Normalize name for better matching.
    """
    if not name:
        return ""
    
    name = str(name).strip().upper()
    
    # Common suffixes that can be ignored for matching
    suffixes_to_remove = [
        'PRIVATE LIMITED', 'PRIVATE LTD', 'PVT LIMITED', 'PVT LTD',
        'LIMITED', 'LTD', 'PVT', 'PRIVATE',
        'COMPANY', 'CO',
        'CORPORATION', 'CORP',
    ]
    
    for suffix in suffixes_to_remove:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
            break  # Only remove one suffix
    
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


def calculate_similarity(name1: str, name2: str) -> int:
    """
    Calculate similarity between two names.
    Uses multiple algorithms and returns the best score.
    """
    if not name1 or not name2:
        return 0
    
    # Quick check: if first 3 chars don't match, likely different
    if len(name1) >= 3 and len(name2) >= 3:
        if name1[:3].upper() != name2[:3].upper():
            # Unless one is a substring of the other
            if name1.upper() not in name2.upper() and name2.upper() not in name1.upper():
                return 0
    
    # Normalize both names
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return 100
    
    # One contains the other
    if norm1 in norm2 or norm2 in norm1:
        longer = max(len(norm1), len(norm2))
        shorter = min(len(norm1), len(norm2))
        if shorter / longer >= 0.7:  # At least 70% overlap
            return 85
    
    upper1 = str(name1).upper().strip()
    upper2 = str(name2).upper().strip()
    
    # Different similarity algorithms
    scores = [
        fuzz.ratio(upper1, upper2),
        fuzz.partial_ratio(upper1, upper2),
        fuzz.token_sort_ratio(norm1, norm2),
    ]
    
    return max(scores)


def group_similar_names(names_list: List[str], threshold: int = 85) -> List[List[str]]:
    """
    Groups similar extracted names together.
    Uses higher threshold to avoid incorrect grouping.
    """
    if not names_list:
        return []
    
    # Remove duplicates while preserving order
    unique_names = []
    seen = set()
    for name in names_list:
        upper_name = str(name).upper().strip()
        if upper_name not in seen and len(upper_name) > 1:
            unique_names.append(name)
            seen.add(upper_name)
    
    # Filter out generic names that shouldn't be grouped
    generic_names = {'CASH', 'BANK CHARGES', 'PAYMENT MADE', 'PAYMENT RECEIPT'}
    
    real_names = [n for n in unique_names if str(n).upper().strip() not in generic_names]
    generic_list = [n for n in unique_names if str(n).upper().strip() in generic_names]
    
    groups = []
    processed = set()
    
    for i, name in enumerate(real_names):
        if i in processed:
            continue
        
        current_group = [name]
        processed.add(i)
        
        # Compare with other unprocessed names
        for j, other_name in enumerate(real_names):
            if j in processed or i == j:
                continue
            
            similarity = calculate_similarity(name, other_name)
            
            if similarity >= threshold:
                current_group.append(other_name)
                processed.add(j)
        
        groups.append(current_group)
    
    # Add generic names as separate single-item groups
    for name in generic_list:
        groups.append([name])
    
    # Sort groups by size (largest first) then alphabetically
    groups.sort(key=lambda g: (-len(g), str(g[0]).upper()))
    
    # Sort names within each group
    for group in groups:
        group.sort(key=lambda n: str(n).upper())
    
    print(f"\n=== Name Grouping Results ===")
    print(f"Input: {len(unique_names)} unique names")
    print(f"Output: {len(groups)} groups")
    for i, group in enumerate(groups):
        if len(group) > 1:
            print(f"  Group {i+1}: {group}")
    
    return groups


def suggest_tally_master(extracted_name: str, tally_ledger_names: List[str]) -> Tuple[Optional[str], int]:
    """Match extracted name against Tally Master ledgers."""
    if not tally_ledger_names or not extracted_name:
        return None, 0
    
    extracted_upper = str(extracted_name).upper().strip()
    
    # Exact match
    for ledger_name in tally_ledger_names:
        if ledger_name.upper().strip() == extracted_upper:
            return ledger_name, 100
    
    # Normalized match
    extracted_normalized = normalize_name(extracted_name)
    for ledger_name in tally_ledger_names:
        if normalize_name(ledger_name) == extracted_normalized:
            return ledger_name, 95
    
    # Fuzzy match
    best_match = None
    best_score = 0
    
    for ledger_name in tally_ledger_names:
        score = calculate_similarity(extracted_name, ledger_name)
        if score > best_score:
            best_score = score
            best_match = ledger_name
    
    if best_score >= 85:
        return best_match, best_score
    
    return None, best_score