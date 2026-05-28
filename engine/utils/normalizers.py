"""Centralized name normalization utilities."""

import re
from typing import Optional


def normalize_name(name: str, remove_suffixes: bool = True) -> str:
    """
    Normalize name for consistent matching across the application.
    
    Args:
        name: Input name to normalize
        remove_suffixes: Whether to remove company suffixes
        
    Returns:
        Normalized name string
    """
    if not name:
        return ""
    
    name = str(name).strip().upper()
    
    # Remove common company suffixes
    if remove_suffixes:
        suffixes = [
            'PRIVATE LIMITED', 'PRIVATE LTD', 'PVT LIMITED', 'PVT LTD',
            'LIMITED', 'LTD', 'PVT', 'PRIVATE',
            'COMPANY', 'CO', 'CORP',
            'CORPORATION', 'INC', 'LLC'
        ]
        
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
                break
    
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


def normalize_party_name(name: str) -> str:
    """
    Normalize party/ledger name for comparison.
    
    Args:
        name: Party/ledger name
        
    Returns:
        Normalized name
    """
    if not name:
        return ""
    
    name = str(name).strip().upper()
    # Remove extra spaces
    name = " ".join(name.split())
    return name


def normalize_date_for_comparison(date_str: str) -> str:
    """
    Normalize date string to YYYYMMDD format for comparison.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Normalized date in YYYYMMDD format or empty string
    """
    if not date_str:
        return ""
    
    date_str = str(date_str).strip()
    
    # Remove time component
    if ' ' in date_str:
        date_str = date_str.split(' ')[0]
    
    # Already in YYYYMMDD format
    if len(date_str) == 8 and date_str.isdigit():
        return date_str
    
    from datetime import datetime
    
    formats = [
        ("%Y-%m-%d", "%Y%m%d"),
        ("%d/%m/%Y", "%Y%m%d"),
        ("%d-%m-%Y", "%Y%m%d"),
        ("%d.%m.%Y", "%Y%m%d"),
        ("%d %b %Y", "%Y%m%d"),
        ("%d-%b-%Y", "%Y%m%d"),
    ]
    
    for parse_fmt, output_fmt in formats:
        try:
            dt = datetime.strptime(date_str[:10], parse_fmt)
            return dt.strftime(output_fmt)
        except ValueError:
            continue
    
    return date_str


def normalize_amount(amount) -> float:
    """
    Normalize amount to float for comparison.
    
    Args:
        amount: Amount value (can be string or number)
        
    Returns:
        Normalized amount as float
    """
    try:
        return round(abs(float(amount)), 2)
    except (ValueError, TypeError):
        return 0.0
