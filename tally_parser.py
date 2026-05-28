# engine/tally_parser.py
"""
Tally XML Parser for Master and Daybook files.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class TallyLedger:
    """Represents a Tally ledger master"""
    name: str
    alias: str = ""
    parent_group: str = ""


@dataclass
class TallyVoucher:
    """Represents a Tally voucher entry"""
    date: str
    voucher_type: str
    party_name: str
    amount: float
    narration: str
    reference: str = ""
    voucher_number: str = ""


class TallyMasterParser:
    """Parse Tally Master XML file"""
    
    def __init__(self):
        self.ledgers: List[TallyLedger] = []
        self.vouchers: List[TallyVoucher] = []
        self.company_name: str = ""
        
    def parse_master_xml(self, filepath: str) -> Dict:
        """Parse Tally Master XML file"""
        try:
            print(f"\n=== Parsing Tally XML: {filepath} ===")
            
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            print(f"Root tag: {root.tag}")
            
            self._parse_company_name(root)
            self._parse_ledgers(root)
            self._parse_vouchers(root)
            
            print(f"\n=== Parsing Complete ===")
            print(f"Ledgers found: {len(self.ledgers)}")
            print(f"Vouchers found: {len(self.vouchers)}")
            
            if self.ledgers:
                print(f"\nSample ledgers:")
                for i, ledger in enumerate(self.ledgers[:10]):
                    print(f"  {i+1}. '{ledger.name}' (Group: '{ledger.parent_group}')")
            
            if self.vouchers:
                print(f"\nSample vouchers:")
                for i, v in enumerate(self.vouchers[:5]):
                    print(f"  {i+1}. Date: {v.date}, Party: {v.party_name}, Amount: {v.amount}")
            
            return {
                'ledgers': self.ledgers,
                'vouchers': self.vouchers,
                'company_name': self.company_name,
                'success': True,
                'error': None
            }
            
        except Exception as e:
            import traceback
            print(f"Error parsing XML: {e}")
            traceback.print_exc()
            return {
                'ledgers': [],
                'vouchers': [],
                'company_name': '',
                'success': False,
                'error': str(e)
            }
    
    def _parse_company_name(self, root):
        """Extract company name"""
        try:
            elem = root.find('.//SVCURRENTCOMPANY')
            if elem is not None and elem.text:
                self.company_name = elem.text.strip()
            else:
                self.company_name = "Company"
            print(f"Company: {self.company_name}")
        except:
            self.company_name = "Company"
    
    def _parse_ledgers(self, root):
        """Parse all ledgers from XML"""
        self.ledgers = []
        ledger_elems = root.findall('.//LEDGER')
        
        print(f"Found {len(ledger_elems)} LEDGER elements")
        
        for ledger in ledger_elems:
            name = ""
            alias = ""
            parent = ""
            
            # Method 1: NAME child element
            name_elem = ledger.find('NAME')
            if name_elem is not None and name_elem.text:
                name = name_elem.text.strip()
            
            # Method 2: NAME attribute on LEDGER element
            if not name:
                name = ledger.get('NAME', '').strip()
            
            # Get PARENT (group)
            parent_elem = ledger.find('PARENT')
            if parent_elem is not None and parent_elem.text:
                parent = parent_elem.text.strip()
            
            # Get ALIASNAME
            alias_elem = ledger.find('ALIASNAME')
            if alias_elem is not None and alias_elem.text:
                alias = alias_elem.text.strip()
            
            if name:
                self.ledgers.append(TallyLedger(name=name, alias=alias, parent_group=parent))
        
        print(f"Successfully parsed {len(self.ledgers)} ledgers")
    
    def _parse_vouchers(self, root):
        """Parse all vouchers from XML"""
        self.vouchers = []
        voucher_elems = root.findall('.//VOUCHER')
        
        print(f"Found {len(voucher_elems)} VOUCHER elements")
        
        for voucher in voucher_elems:
            v = self._extract_voucher_data(voucher)
            if v:
                self.vouchers.append(v)
    
    def _extract_voucher_data(self, voucher) -> Optional[TallyVoucher]:
        """Extract voucher data - FIXED parameter names"""
        try:
            # Get all elements
            date_elem = voucher.find('DATE')
            vtype_elem = voucher.find('VOUCHERTYPENAME')
            party_elem = voucher.find('PARTYLEDGERNAME')
            ref_elem = voucher.find('REFERENCE')
            narr_elem = voucher.find('NARRATION')
            vnum_elem = voucher.find('VOUCHERNUMBER')
            
            # Extract text values
            date_str = date_elem.text if date_elem is not None else ""
            vtype_str = vtype_elem.text if vtype_elem is not None else ""
            party_str = party_elem.text if party_elem is not None else ""
            ref_str = ref_elem.text if ref_elem is not None else ""
            narr_str = narr_elem.text if narr_elem is not None else ""
            vnum_str = vnum_elem.text if vnum_elem is not None else ""
            
            # Calculate amount from ledger entries
            amount = 0.0
            
            # Tally 9 format - ALLLEDGERENTRIES.LIST
            for entries in voucher.findall('.//ALLLEDGERENTRIES.LIST'):
                amt_elem = entries.find('AMOUNT')
                if amt_elem is not None and amt_elem.text:
                    try:
                        amt = abs(float(amt_elem.text))
                        if amt > amount:
                            amount = amt
                    except ValueError:
                        pass
            
            # Tally Prime format - LEDGERENTRIES.LIST
            if amount == 0:
                for entries in voucher.findall('.//LEDGERENTRIES.LIST'):
                    amt_elem = entries.find('AMOUNT')
                    if amt_elem is not None and amt_elem.text:
                        try:
                            amt = abs(float(amt_elem.text))
                            if amt > amount:
                                amount = amt
                        except ValueError:
                            pass
            
            # Create voucher object with CORRECT parameter names
            return TallyVoucher(
                date=date_str,
                voucher_type=vtype_str,
                party_name=party_str,  # FIXED: was 'party' before
                amount=amount,
                narration=narr_str,
                reference=ref_str,
                voucher_number=vnum_str
            )
            
        except Exception as e:
            import traceback
            print(f"Error extracting voucher: {e}")
            traceback.print_exc()
            return None
    
    def get_ledger_names(self) -> List[str]:
        """Return list of ledger names only"""
        names = [ledger.name for ledger in self.ledgers if ledger.name]
        print(f"Returning {len(names)} ledger names")
        return names
    
    def get_ledger_dict(self) -> Dict[str, TallyLedger]:
        """Return dictionary of ledger name -> TallyLedger"""
        return {ledger.name.upper(): ledger for ledger in self.ledgers if ledger.name}


def normalize_date_for_comparison(date_str: str) -> str:
    """Normalize date string to YYYYMMDD format"""
    if not date_str:
        return ""
    
    date_str = str(date_str).strip()
    
    # Remove time component if present
    if ' ' in date_str:
        date_str = date_str.split(' ')[0]
    
    # Already in YYYYMMDD format (8 digits)
    if len(date_str) == 8 and date_str.isdigit():
        return date_str
    
    # Try various formats
    formats = [
        ("%Y-%m-%d", "%Y%m%d"),
        ("%d/%m/%Y", "%Y%m%d"),
        ("%d-%m-%Y", "%Y%m%d"),
        ("%d.%m.%Y", "%Y%m%d"),
        ("%Y/%m/%d", "%Y%m%d"),
        ("%d %b %Y", "%Y%m%d"),
        ("%d-%b-%Y", "%Y%m%d"),
    ]
    
    for parse_fmt, output_fmt in formats:
        try:
            dt = datetime.strptime(date_str[:10], parse_fmt)
            return dt.strftime(output_fmt)
        except ValueError:
            continue
    
    print(f"WARNING: Could not parse date '{date_str}'")
    return date_str


def normalize_amount(amount) -> float:
    """Normalize amount for comparison"""
    try:
        return round(abs(float(amount)), 2)
    except (ValueError, TypeError):
        return 0.0


def normalize_party_name(name: str) -> str:
    """Normalize party name for comparison"""
    if not name:
        return ""
    
    name = str(name).strip().upper()
    
    # Remove extra spaces
    name = " ".join(name.split())
    
    return name


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
    """
    duplicates = []
    
    # Normalize input values
    trans_date_norm = normalize_date_for_comparison(transaction_date)
    trans_amount_norm = normalize_amount(amount)
    trans_party_norm = normalize_party_name(party_name)
    
    print(f"\n=== Duplicate Check ===")
    print(f"Input: Date={transaction_date} -> {trans_date_norm}, Amount={trans_amount_norm}, Party={trans_party_norm}")
    print(f"Checking against {len(daybook_vouchers)} daybook entries")
    
    for voucher in daybook_vouchers:
        # Normalize voucher values
        voucher_date_norm = normalize_date_for_comparison(voucher.date)
        voucher_amount_norm = normalize_amount(voucher.amount)
        voucher_party_norm = normalize_party_name(voucher.party_name)
        
        # Check party name (most important) - exact match
        if trans_party_norm != voucher_party_norm:
            continue
        
        # Check amount (within tolerance)
        amount_match = abs(trans_amount_norm - voucher_amount_norm) <= amount_tolerance
        
        # Check date (within tolerance)
        date_match = False
        if trans_date_norm and voucher_date_norm:
            try:
                # Compare as integers
                date_diff = abs(int(trans_date_norm) - int(voucher_date_norm))
                date_match = date_diff <= date_tolerance_days
            except:
                date_match = trans_date_norm == voucher_date_norm
        
        if amount_match and date_match:
            duplicates.append(voucher)
            print(f"  DUPLICATE: {voucher.date} | {voucher.party_name} | {voucher.amount}")
    
    if not duplicates:
        print(f"  No duplicate found")
    else:
        print(f"  Found {len(duplicates)} duplicate(s)")
    
    return duplicates