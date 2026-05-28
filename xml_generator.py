# engine/xml_generator.py
"""
Tally XML Generator for Masters and Vouchers.
Supports Tally.ERP 9 format.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional
import os
import re


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


def parse_date_tally(date_input):
    """
    Parse date to Tally format (YYYYMMDD).
    PRESERVES ORIGINAL DATE - does not modify year.
    """
    # Handle None
    if date_input is None:
        print("WARNING: date_input is None")
        return None
    
    # If already datetime object
    if isinstance(date_input, datetime):
        result = date_input.strftime("%Y%m%d")
        print(f"DEBUG: datetime object -> {result}")
        return result
    
    # If pandas Timestamp
    if hasattr(date_input, 'strftime'):
        result = date_input.strftime("%Y%m%d")
        print(f"DEBUG: Timestamp object -> {result}")
        return result
    
    # Convert to string and strip
    date_str = str(date_input).strip()
    
    print(f"DEBUG: parse_date_tally input = '{date_str}'")
    
    # Check for empty string
    if not date_str or date_str == '' or date_str == 'nan' or date_str == 'None':
        print(f"DEBUG: Empty date string")
        return None
    
    # Remove time component if present
    if ' ' in date_str:
        date_str = date_str.split(' ')[0].strip()
    
    # Remove .0 suffix (from pandas numeric conversion)
    if date_str.endswith('.0'):
        date_str = date_str[:-2]
    
    # YYYYMMDD format (8 digits only)
    if len(date_str) == 8 and date_str.isdigit():
        year = int(date_str[:4])
        if 1900 <= year <= 2100:
            print(f"DEBUG: Already YYYYMMDD -> {date_str}")
            return date_str
    
    # DD-MM-YYYY format (10 chars with dashes at positions 2 and 5)
    if len(date_str) == 10 and date_str[2] == '-' and date_str[5] == '-':
        try:
            day = int(date_str[0:2])
            month = int(date_str[3:5])
            year = int(date_str[6:10])
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                result = f"{year:04d}{month:02d}{day:02d}"
                print(f"DEBUG: DD-MM-YYYY -> {date_str} = {result}")
                return result
        except:
            pass
    
    # DD/MM/YYYY format
    if len(date_str) == 10 and date_str[2] == '/' and date_str[5] == '/':
        try:
            day = int(date_str[0:2])
            month = int(date_str[3:5])
            year = int(date_str[6:10])
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                result = f"{year:04d}{month:02d}{day:02d}"
                print(f"DEBUG: DD/MM/YYYY -> {date_str} = {result}")
                return result
        except:
            pass
    
    # YYYY-MM-DD format
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        try:
            year = int(date_str[0:4])
            month = int(date_str[5:7])
            day = int(date_str[8:10])
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                result = f"{year:04d}{month:02d}{day:02d}"
                print(f"DEBUG: YYYY-MM-DD -> {date_str} = {result}")
                return result
        except:
            pass
    
    # DD.MM.YYYY format
    if len(date_str) == 10 and date_str[2] == '.' and date_str[5] == '.':
        try:
            day = int(date_str[0:2])
            month = int(date_str[3:5])
            year = int(date_str[6:10])
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                result = f"{year:04d}{month:02d}{day:02d}"
                print(f"DEBUG: DD.MM.YYYY -> {date_str} = {result}")
                return result
        except:
            pass
    
    # Try datetime parsing for various formats
    date_formats = [
        "%d-%m-%Y",
        "%d/%m/%Y", 
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d-%b-%Y",
        "%d %b %Y",
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            result = dt.strftime("%Y%m%d")
            print(f"DEBUG: Parsed with {fmt} -> {date_str} = {result}")
            return result
        except:
            continue
    
    # If we get here, we couldn't parse
    print(f"WARNING: Could not parse date '{date_input}', returning None")
    return None


def is_valid_ledger_name(name):
    """Check if ledger name is valid"""
    if not name:
        return False
    name = str(name).strip()
    if name == '':
        return False
    if name in ['Unknown Transaction', 'Unknown', 'None']:
        return False
    if name.lower() in ['none', 'null', 'nan']:
        return False
    return True


class TallyXMLGenerator:
    """Generate Tally-compatible XML files."""
    
    def __init__(self, company_name="", bank_ledger_name="Bank Account"):
        self.company_name = company_name
        self.bank_ledger_name = bank_ledger_name
    
    def generate_masters_xml(self, new_ledgers, ledger_groups, output_path, tally_version="9"):
        """Generate Masters XML file"""
        try:
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
            
            lines.extend([
                '      </REQUESTDATA>',
                '    </IMPORTDATA>',
                '  </BODY>',
                '</ENVELOPE>'
            ])
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return {'success': True, 'path': output_path, 'ledger_count': len(new_ledgers)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_vouchers_xml(self, transactions, output_path):
        """Generate Vouchers XML file"""
        try:
            print(f"\n=== Generating Vouchers XML ===")
            print(f"Total transactions: {len(transactions)}")
            
            # Sort transactions by date (handle None dates)
            def sort_key(x):
                d = x.get('date', '')
                return d if d else '99999999'
            
            transactions = sorted(transactions, key=sort_key)
            
            xml_content, count, skips, logs = self._build_xml(transactions)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print(f"\n=== XML Generated Successfully ===")
            print(f"Vouchers created: {count}")
            print(f"Skipped: {skips}")
            
            return {
                'success': True,
                'path': output_path,
                'voucher_count': count,
                'total_count': len(transactions),
                'skip_count': skips
            }
            
        except Exception as e:
            import traceback
            print(f"ERROR: {e}")
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _build_xml(self, transactions):
        """Build XML content"""
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
        logs = []
        
        for idx, trans in enumerate(transactions, 1):
            try:
                # Parse date
                raw_date = trans.get('date', '')
                td = parse_date_tally(raw_date)
                
                if not td:
                    logs.append(f"Row {idx}: Bad date - raw: '{raw_date}'")
                    print(f"WARNING: Skipping row {idx} due to bad date: '{raw_date}'")
                    continue
                
                amount = round(abs(float(trans.get('amount', 0))), 2)
                if amount == 0:
                    logs.append(f"Row {idx}: Zero amount")
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
                lines.append(f'            <NARRATION>{esc(vtype)} - {esc(str(narr))[:150]}</NARRATION>')
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
                        # Cash Deposit - Bank Dr, Cash Cr
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
                        # Cash Withdrawal - Cash Dr, Bank Cr
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
                vc += 1
                
            except Exception as e:
                logs.append(f"Row {idx}: Error - {str(e)}")
                print(f"ERROR on row {idx}: {e}")
                continue
        
        lines.extend([
            '      </REQUESTDATA>',
            '    </IMPORTDATA>',
            '  </BODY>',
            '</ENVELOPE>'
        ])
        
        return '\n'.join(lines), vc, len(logs), logs