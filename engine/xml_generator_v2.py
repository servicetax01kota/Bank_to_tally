"""Enhanced Tally XML Generator with duplicate prevention.
Improved version with better ledger management and voucher generation.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os
import re
from engine.utils.normalizers import normalize_party_name, normalize_date_for_comparison
from engine.utils.validators import is_valid_ledger_name, validate_ledger_for_tally, validate_transactions
from engine.utils.logger import AuditLogger


def esc(text):
    """Escape special XML characters"""
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)
    return text


def parse_date_tally(date_input) -> Optional[str]:
    """
    Parse date to Tally format (YYYYMMDD).
    Preserves original date - does not modify year.
    
    Args:
        date_input: Date in various formats
        
    Returns:
        Date in YYYYMMDD format or None
    """
    if date_input is None:
        return None
    
    # Handle datetime object
    if isinstance(date_input, datetime):
        return date_input.strftime("%Y%m%d")
    
    # Handle pandas Timestamp
    if hasattr(date_input, 'strftime'):
        return date_input.strftime("%Y%m%d")
    
    date_str = str(date_input).strip()
    
    # Check for empty string
    if not date_str or date_str in ['nan', 'None', 'NaT', '<NA>']:
        return None
    
    # Remove time component
    if ' ' in date_str:
        date_str = date_str.split(' ')[0].strip()
    
    # Remove .0 suffix
    if date_str.endswith('.0'):
        date_str = date_str[:-2]
    
    # Already YYYYMMDD format
    if len(date_str) == 8 and date_str.isdigit():
        year = int(date_str[:4])
        if 1900 <= year <= 2100:
            return date_str
    
    # DD-MM-YYYY format
    if len(date_str) == 10 and date_str[2] == '-' and date_str[5] == '-':
        try:
            day = int(date_str[0:2])
            month = int(date_str[3:5])
            year = int(date_str[6:10])
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                return f"{year:04d}{month:02d}{day:02d}"
        except:
            pass
    
    # DD/MM/YYYY format
    if len(date_str) == 10 and date_str[2] == '/' and date_str[5] == '/':
        try:
            day = int(date_str[0:2])
            month = int(date_str[3:5])
            year = int(date_str[6:10])
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                return f"{year:04d}{month:02d}{day:02d}"
        except:
            pass
    
    # YYYY-MM-DD format
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        try:
            year = int(date_str[0:4])
            month = int(date_str[5:7])
            day = int(date_str[8:10])
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                return f"{year:04d}{month:02d}{day:02d}"
        except:
            pass
    
    # DD.MM.YYYY format
    if len(date_str) == 10 and date_str[2] == '.' and date_str[5] == '.':
        try:
            day = int(date_str[0:2])
            month = int(date_str[3:5])
            year = int(date_str[6:10])
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                return f"{year:04d}{month:02d}{day:02d}"
        except:
            pass
    
    # Try various datetime formats
    date_formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y",
        "%d-%b-%Y", "%d %b %Y",
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y%m%d")
        except:
            continue
    
    return None


class TallyXMLGenerator:
    """Generate Tally-compatible XML files with duplicate prevention."""
    
    def __init__(self, company_name: str = "", 
                 bank_ledger_name: str = "Bank Account",
                 existing_ledger_names: List[str] = None,
                 audit_logger: AuditLogger = None):
        """
        Initialize XML generator.
        
        Args:
            company_name: Tally company name
            bank_ledger_name: Bank account ledger name
            existing_ledger_names: List of existing Tally ledger names (for duplicate prevention)
            audit_logger: Audit logger instance
        """
        self.company_name = company_name
        self.bank_ledger_name = bank_ledger_name
        self.existing_ledger_names = set([
            n.upper().strip() for n in (existing_ledger_names or [])
        ])
        self.audit_logger = audit_logger
        
        self.skipped_ledgers = []
        self.created_ledgers = []
        self.skipped_vouchers = []
        self.created_vouchers = []
    
    def generate_masters_xml(self, new_ledgers: List[str], 
                            ledger_groups: Dict[str, str],
                            output_path: str,
                            tally_version: str = "9") -> Dict:
        """
        Generate Masters XML file with duplicate prevention.
        **KEY FEATURE: Checks existing ledgers before adding to XML**
        
        Args:
            new_ledgers: List of new ledger names to create
            ledger_groups: Dict mapping ledger names to parent groups
            output_path: Output file path
            tally_version: Tally version (9 or Prime)
            
        Returns:
            Result dictionary with success status
        """
        try:
            print(f"\n=== Generating Masters XML ===")
            print(f"Input ledgers: {len(new_ledgers)}")
            print(f"Existing ledgers in Tally: {len(self.existing_ledger_names)}")
            
            lines = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<ENVELOPE>',
                '  <HEADER>',
                '    <TALLYREQUEST>Import Data</TALLYREQUEST>',
                '  </HEADER>',
                '  <BODY>',
                '    <IMPORTDATA>',
                '      <REQUESTDESC>',
                '        <REPORTNAME>All Masters</REPORTNAME>',
                '        <STATICVARIABLES>',
                f'          <SVCURRENTCOMPANY>{esc(self.company_name)}</SVCURRENTCOMPANY>',
                '        </STATICVARIABLES>',
                '      </REQUESTDESC>',
                '      <REQUESTDATA>'
            ]
            
            for ledger_name in new_ledgers:
                if not is_valid_ledger_name(ledger_name):
                    self.skipped_ledgers.append((ledger_name, "Invalid name"))
                    if self.audit_logger:
                        self.audit_logger.log_ledger_skipped(ledger_name, "Invalid name")
                    continue
                
                # **CRITICAL: Check for duplicate in existing Tally ledgers**
                ledger_upper = ledger_name.upper().strip()
                if ledger_upper in self.existing_ledger_names:
                    self.skipped_ledgers.append((ledger_name, "Already exists in Tally"))
                    print(f"  ✗ SKIP: '{ledger_name}' (already exists in Tally)")
                    if self.audit_logger:
                        self.audit_logger.log_ledger_skipped(ledger_name, "Already exists in Tally")
                    continue
                
                group = ledger_groups.get(ledger_name, "Sundry Debtors")
                rid = str(uuid.uuid4())
                
                lines.append(f'        <TALLYMESSAGE xmlns:UDF="TallyUDF">')
                lines.append(f'          <LEDGER REMOTEID="{rid}" NAME="{esc(ledger_name)}" ACTION="Create">')
                lines.append(f'            <NAME>{esc(ledger_name)}</NAME>')
                lines.append(f'            <PARENT>{esc(group)}</PARENT>')
                lines.append(f'            <ISBILLWISEON>Yes</ISBILLWISEON>')
                lines.append(f'          </LEDGER>')
                lines.append(f'        </TALLYMESSAGE>')
                
                self.created_ledgers.append((ledger_name, group))
                print(f"  ✓ CREATE: '{ledger_name}' → {group}")
                
                if self.audit_logger:
                    self.audit_logger.log_ledger_created(ledger_name, group)
            
            lines.extend([
                '      </REQUESTDATA>',
                '    </IMPORTDATA>',
                '  </BODY>',
                '</ENVELOPE>'
            ])
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print(f"\n═══ Masters XML Summary ═══")
            print(f"  ✓ Created: {len(self.created_ledgers)} ledgers")
            print(f"  ✗ Skipped: {len(self.skipped_ledgers)} ledgers (duplicates prevented)")
            print(f"  📄 File: {output_path}")
            
            return {
                'success': True,
                'path': output_path,
                'ledger_count': len(self.created_ledgers),
                'skipped_count': len(self.skipped_ledgers),
                'skipped_ledgers': self.skipped_ledgers
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_vouchers_xml(self, transactions: List[Dict],
                             output_path: str,
                             existing_voucher_check=None) -> Dict:
        """
        Generate Vouchers XML file.
        
        Args:
            transactions: List of transaction dictionaries
            output_path: Output file path
            existing_voucher_check: Optional function to check for existing vouchers
            
        Returns:
            Result dictionary with success status
        """
        try:
            print(f"\n=== Generating Vouchers XML ===")
            print(f"Total transactions: {len(transactions)}")
            
            # Validate transactions
            valid_trans, errors = validate_transactions(transactions)
            
            if errors:
                print(f"\n⚠️  Validation errors ({len(errors)}):")
                for error in errors[:10]:  # Show first 10
                    print(f"   {error}")
                if len(errors) > 10:
                    print(f"   ... and {len(errors) - 10} more")
            
            # Sort by date
            valid_trans.sort(key=lambda x: x.get('date', ''))
            
            lines = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<ENVELOPE>',
                '  <HEADER>',
                '    <TALLYREQUEST>Import Data</TALLYREQUEST>',
                '  </HEADER>',
                '  <BODY>',
                '    <IMPORTDATA>',
                '      <REQUESTDESC>',
                '        <REPORTNAME>Vouchers</REPORTNAME>',
                '        <STATICVARIABLES>',
                f'          <SVCURRENTCOMPANY>{esc(self.company_name)}</SVCURRENTCOMPANY>',
                '        </STATICVARIABLES>',
                '      </REQUESTDESC>',
                '      <REQUESTDATA>'
            ]
            
            vc = 0
            
            for idx, trans in enumerate(valid_trans, 1):
                try:
                    # Parse date
                    raw_date = trans.get('date', '')
                    td = parse_date_tally(raw_date)
                    
                    if not td:
                        self.skipped_vouchers.append((idx, "Invalid date", raw_date))
                        if self.audit_logger:
                            self.audit_logger.log_event('VOUCHER_SKIPPED', {
                                'index': idx,
                                'reason': 'Invalid date'
                            })
                        continue
                    
                    amount = round(abs(float(trans.get('amount', 0))), 2)
                    if amount == 0:
                        self.skipped_vouchers.append((idx, "Zero amount", ""))
                        continue
                    
                    party = trans.get('mapped_ledger', '') or trans.get('extracted_name', 'Cash')
                    if not is_valid_ledger_name(party):
                        party = "Cash"
                    party = str(party).strip()
                    
                    ref = trans.get('reference', '')
                    narr = trans.get('narration', '')
                    ttype = trans.get('type', 'Payment')
                    
                    # Determine voucher type
                    if 'CASH' in party.upper() or ttype == 'Cash':
                        vtype = 'Contra'
                    elif ttype == 'Receipt':
                        vtype = 'Receipt'
                    else:
                        vtype = 'Payment'
                    
                    rid = str(uuid.uuid4())
                    
                    lines.append(f'        <TALLYMESSAGE xmlns:UDF="TallyUDF">')
                    lines.append(f'          <VOUCHER REMOTEID="{rid}" VCHTYPE="{vtype}" ACTION="Create">')
                    lines.append(f'            <DATE>{td}</DATE>')
                    lines.append(f'            <EFFECTIVEDATE>{td}</EFFECTIVEDATE>')
                    lines.append(f'            <VOUCHERTYPENAME>{esc(vtype)}</VOUCHERTYPENAME>')
                    lines.append(f'            <REFERENCE>{esc(str(ref))}</REFERENCE>')
                    lines.append(f'            <VOUCHERNUMBER>{vc+1}</VOUCHERNUMBER>')
                    lines.append(f'            <PARTYLEDGERNAME>{esc(party)}</PARTYLEDGERNAME>')
                    lines.append(f'            <NARRATION>{esc(vtype)} - {esc(str(narr)[:150])}</NARRATION>')
                    lines.append(f'            <ISINVOICE>No</ISINVOICE>')
                    lines.append(f'            <PERSISTEDVIEW>None</PERSISTEDVIEW>')
                    
                    bank = self.bank_ledger_name
                    
                    if vtype == 'Payment':
                        # Party Dr, Bank Cr
                        lines.append(f'            <ALLLEDGERENTRIES.LIST>')
                        lines.append(f'              <LEDGERNAME>{esc(party)}</LEDGERNAME>')
                        lines.append(f'              <ISDEBIT>Yes</ISDEBIT>')
                        lines.append(f'              <AMOUNT>{amount:.2f}</AMOUNT>')
                        lines.append(f'            </ALLLEDGERENTRIES.LIST>')
                        
                        lines.append(f'            <ALLLEDGERENTRIES.LIST>')
                        lines.append(f'              <LEDGERNAME>{esc(bank)}</LEDGERNAME>')
                        lines.append(f'              <ISDEBIT>No</ISDEBIT>')
                        lines.append(f'              <AMOUNT>-{amount:.2f}</AMOUNT>')
                        lines.append(f'            </ALLLEDGERENTRIES.LIST>')
                        
                    elif vtype == 'Receipt':
                        # Bank Dr, Party Cr
                        lines.append(f'            <ALLLEDGERENTRIES.LIST>')
                        lines.append(f'              <LEDGERNAME>{esc(bank)}</LEDGERNAME>')
                        lines.append(f'              <ISDEBIT>Yes</ISDEBIT>')
                        lines.append(f'              <AMOUNT>{amount:.2f}</AMOUNT>')
                        lines.append(f'            </ALLLEDGERENTRIES.LIST>')
                        
                        lines.append(f'            <ALLLEDGERENTRIES.LIST>')
                        lines.append(f'              <LEDGERNAME>{esc(party)}</LEDGERNAME>')
                        lines.append(f'              <ISDEBIT>No</ISDEBIT>')
                        lines.append(f'              <AMOUNT>-{amount:.2f}</AMOUNT>')
                        lines.append(f'            </ALLLEDGERENTRIES.LIST>')
                        
                    elif vtype == 'Contra':
                        # Cash transactions
                        if 'DEPOSIT' in str(narr).upper() or ttype == 'Receipt':
                            # Cash Deposit
                            lines.append(f'            <ALLLEDGERENTRIES.LIST>')
                            lines.append(f'              <LEDGERNAME>{esc(bank)}</LEDGERNAME>')
                            lines.append(f'              <ISDEBIT>Yes</ISDEBIT>')
                            lines.append(f'              <AMOUNT>{amount:.2f}</AMOUNT>')
                            lines.append(f'            </ALLLEDGERENTRIES.LIST>')
                            
                            lines.append(f'            <ALLLEDGERENTRIES.LIST>')
                            lines.append(f'              <LEDGERNAME>Cash</LEDGERNAME>')
                            lines.append(f'              <ISDEBIT>No</ISDEBIT>')
                            lines.append(f'              <AMOUNT>-{amount:.2f}</AMOUNT>')
                            lines.append(f'            </ALLLEDGERENTRIES.LIST>')
                        else:
                            # Cash Withdrawal
                            lines.append(f'            <ALLLEDGERENTRIES.LIST>')
                            lines.append(f'              <LEDGERNAME>Cash</LEDGERNAME>')
                            lines.append(f'              <ISDEBIT>Yes</ISDEBIT>')
                            lines.append(f'              <AMOUNT>{amount:.2f}</AMOUNT>')
                            lines.append(f'            </ALLLEDGERENTRIES.LIST>')
                            
                            lines.append(f'            <ALLLEDGERENTRIES.LIST>')
                            lines.append(f'              <LEDGERNAME>{esc(bank)}</LEDGERNAME>')
                            lines.append(f'              <ISDEBIT>No</ISDEBIT>')
                            lines.append(f'              <AMOUNT>-{amount:.2f}</AMOUNT>')
                            lines.append(f'            </ALLLEDGERENTRIES.LIST>')
                    
                    lines.append(f'          </VOUCHER>')
                    lines.append(f'        </TALLYMESSAGE>')
                    
                    self.created_vouchers.append({
                        'party': party,
                        'amount': amount,
                        'date': td
                    })
                    vc += 1
                    
                except Exception as e:
                    self.skipped_vouchers.append((idx, str(e), ""))
                    print(f"  ✗ ERROR: Row {idx}: {e}")
                    continue
            
            lines.extend([
                '      </REQUESTDATA>',
                '    </IMPORTDATA>',
                '  </BODY>',
                '</ENVELOPE>'
            ])
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print(f"\n═══ Vouchers XML Summary ═══")
            print(f"  ✓ Created: {vc} vouchers")
            print(f"  ✗ Skipped: {len(self.skipped_vouchers)} vouchers")
            print(f"  📄 File: {output_path}")
            
            return {
                'success': True,
                'path': output_path,
                'voucher_count': vc,
                'total_count': len(valid_trans),
                'skip_count': len(self.skipped_vouchers),
                'skipped_vouchers': self.skipped_vouchers
            }
            
        except Exception as e:
            import traceback
            print(f"ERROR: {e}")
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
