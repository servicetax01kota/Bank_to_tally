# engine/banks/sbi_current.py
"""
State Bank of India (SBI) Current Account Parser
"""

import re

BANK_NAME = "State Bank of India (SBI)"
BANK_ID = "sbi_current"


def extract(narration):
    """
    Extract party name from SBI Current Account narration.
    """
    if not narration:
        return None
    
    narration = str(narration).strip()
    upper_n = narration.upper()
    
    # CASH RELATED
    if any(keyword in upper_n for keyword in ['CASH CHEQUE', 'CASH WDL', 'CASH WITHDRAWAL', 'CASH DEPOSIT']):
        return 'Cash'
    
    # BANK CHARGES / ATM
    if any(keyword in upper_n for keyword in ['ATMCARD', 'ATM CARD', 'AMC ', 'CHARGES', 'CHG ', 'FEE']):
        return 'Bank Charges'
    
    # ============================================
    # NEFT FORMATS
    # ============================================
    if 'BY TRANSFER-NEFT' in upper_n or 'NEFT*' in upper_n:
        parts = narration.split('*')
        
        name_parts = []
        
        for i, part in enumerate(parts):
            part = part.strip()
            part_upper = part.upper()
            
            # Skip empty parts
            if not part:
                continue
            
            # Skip prefix parts
            if part_upper in ['BY TRANSFER-NEFT', 'NEFT', 'BY TRANSFER', '']:
                continue
            
            # Skip IFS/bank codes (11 chars: 4 letters + digit + 6 alphanumeric)
            if re.match(r'^[A-Z]{4}[0-9][A-Z0-9]{6}$', part_upper) and len(part_upper) == 11:
                continue
            
            # Skip shorter bank codes (4 letters + 4+ digits)
            if re.match(r'^[A-Z]{4}\d{4,}$', part_upper):
                continue
            
            # Skip UTR/reference numbers (4+ letters + 6+ digits, 10+ chars)
            if re.match(r'^[A-Z]{4,}\d{6,}$', part_upper) and len(part_upper) >= 10:
                continue
            
            # Skip numeric-only reference numbers (6+ digits)
            if part_upper.isdigit() and len(part_upper) >= 6:
                continue
            
            # Skip suffix codes (2-4 char alphanumeric like BATC, BATCH)
            # These are NOT names, they are branch/batch codes
            if re.match(r'^[A-Z]{2,4}$', part_upper) and not re.search(r'[AEIOU]{2,}', part_upper):
                continue
            
            # Skip parts starting with -- or just --
            if part_upper.startswith('--') or part_upper == '--':
                continue
            
            # Valid name part: contains letters and reasonable length
            if re.search(r'[A-Za-z]{2,}', part) and len(part) > 2:
                clean_part = re.sub(r'-+$', '', part).strip()
                if clean_part:
                    name_parts.append(clean_part)
        
        # If we found name parts, join and return
        if name_parts:
            name = ' '.join(name_parts).strip()
            name = re.sub(r'-+$', '', name).strip()
            if name and len(name) > 2:
                return _clean_party_name(name)
        
        # Fallback: Get name by finding position after UTR
        parts_clean = [p.strip() for p in parts if p.strip() and p.strip() != '--']
        
        # Find the UTR position
        utr_idx = -1
        for i, p in enumerate(parts_clean):
            if re.match(r'^[A-Z]{4,}\d{6,}$', p.upper()) and len(p) >= 10:
                utr_idx = i
                break
        
        if utr_idx >= 0:
            # Name should be after UTR, before any 2-4 char suffix
            for i in range(utr_idx + 1, len(parts_clean)):
                p = parts_clean[i]
                p_upper = p.upper()
                
                # Skip short suffix codes (BATC, etc.)
                if re.match(r'^[A-Z]{2,4}$', p_upper):
                    continue
                
                # Skip if starts with --
                if p_upper.startswith('--'):
                    continue
                
                # This should be the name
                if re.search(r'[A-Za-z]{2,}', p) and len(p) > 2:
                    return _clean_party_name(p)
    
    # ============================================
    # NEFT - Standard format (non-IFS code)
    # ============================================
    if 'NEFT*' in upper_n:
        neft_match = re.search(r'NEFT\*[^*]+\*[^*]+\*([^*]+)--', narration)
        if neft_match:
            party = neft_match.group(1).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # NEFT - UTR format
    # ============================================
    if 'NEFT' in upper_n and 'UTR' in upper_n:
        neft_utr_match = re.search(r'NEFT\s*UTR\s*NO:\s*\w+--\s*\d*\s*(.+)', narration)
        if neft_utr_match:
            party = neft_utr_match.group(1).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # UPI - CREDIT
    # ============================================
    if 'UPI/CR/' in upper_n:
        upi_match = re.search(r'UPI/CR/(\d+)/([^/]+)/', narration)
        if upi_match:
            party = upi_match.group(2).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # UPI - DEBIT
    # ============================================
    if 'UPI/DR/' in upper_n:
        upi_match = re.search(r'UPI/DR/(\d+)/([^/]+)/', narration)
        if upi_match:
            party = upi_match.group(2).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # UPI - Generic
    # ============================================
    if '/UPI/' in upper_n:
        upi_generic = re.search(r'UPI/(?:CR|DR)/([^/]+)/([^/]+)/', narration)
        if upi_generic:
            party = upi_generic.group(2).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # RTGS
    # ============================================
    if 'RTGS' in upper_n:
        rtgs_match = re.search(r'RTGS\s*(?:UTR\s*NO)?\s*:?\s*\w+--([A-Z][A-Za-z0-9\s\.\-]+)', narration)
        if rtgs_match:
            party = rtgs_match.group(1).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # CHQ TRANSFER
    # ============================================
    if 'CHQ TRANSFER' in upper_n:
        chq_match = re.search(r'CHQ\s+TRANSFER.*--\s*\d+\s+(.+)', narration)
        if chq_match:
            party = chq_match.group(1).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # DEBIT-CMP
    # ============================================
    if 'DEBIT-CMP' in upper_n or ('CMP' in upper_n and 'MANDATE' in upper_n):
        cmp_match = re.search(
            r'DEBIT[- ]CMP\s+(?:MANDATE\s+)?(?:DEBIT\s+)?([A-Z][A-Za-z0-9\s\.\-]+?)(?:\s*-\s*DD|--)', 
            narration
        )
        if cmp_match:
            party = cmp_match.group(1).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # BY TRANSFER-CMP
    # ============================================
    if 'TRANSFER-CMP' in upper_n:
        cmp_by_match = re.search(r'TRANSFER[- ]CMP\s+(.+?)--', narration)
        if cmp_by_match:
            party = cmp_by_match.group(1).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # TO CLEARING
    # ============================================
    if 'TO CLEARING' in upper_n:
        clearing_match = re.search(r'TO\s+CLEARING-Chq(?:\s+No\.?)?\s+\d+\s+(.+?)--\d+', narration)
        if clearing_match:
            party = clearing_match.group(1).strip()
            party = re.sub(r'^(?:ICI|CHQ|SESS\s+\d+)\s+', '', party, flags=re.IGNORECASE).strip()
            party = re.sub(r'\s+[A-Z]?\s*\d[\d\s]*$', '', party).strip()
            cleaned = _clean_party_name(party)
            if cleaned:
                return cleaned
    
    # ============================================
    # CHEQUE WDL - No identifiable party
    # ============================================
    if 'CHEQUE WDL' in upper_n:
        return None
    
    # ============================================
    # CHEQUE DEPOSIT - No identifiable party
    # ============================================
    if 'CHEQUE DEPOSIT' in upper_n:
        return None
    
    # ============================================
    # CATCH ALL
    # ============================================
    last_segment = re.search(r'--([A-Z][A-Za-z0-9\s\.]+?)(?:--|$)', narration)
    if last_segment:
        party = last_segment.group(1).strip()
        cleaned = _clean_party_name(party)
        if cleaned and len(cleaned) > 2:
            return cleaned
    
    return None


def is_bank_code(text):
    """Check if text looks like a bank/IFS code."""
    text = text.strip().upper()
    
    # Standard IFS code: exactly 11 chars
    if re.match(r'^[A-Z]{4}[0-9][A-Z0-9]{6}$', text) and len(text) == 11:
        return True
    
    # Short bank codes
    if re.match(r'^[A-Z]{4,6}$', text):
        return True
    
    # Bank codes with numbers
    if re.match(r'^[A-Z]{4}\d{4,}$', text):
        return True
    
    return False


def is_reference_number(text):
    """Check if text looks like a UTR/reference number."""
    text = text.strip().upper()
    
    # UTR pattern
    if re.match(r'^[A-Z]{4,}\d{6,}$', text) and len(text) >= 10:
        return True
    
    # Pure numeric reference
    if text.isdigit() and len(text) >= 6:
        return True
    
    return False


def _clean_party_name(name):
    """Clean extracted party name."""
    if not name:
        return None
    
    name = name.strip()
    
    # Remove trailing dashes
    name = re.sub(r'-+$', '', name)
    
    # Remove trailing reference numbers
    name = re.sub(r'\s+\d{4,}$', '', name)
    
    # Remove common prefixes
    name = re.sub(r'^(?:ICI|CHQ|BY|TO|NO\.?)\s+', '', name, flags=re.IGNORECASE)
    
    # Remove trailing special chars
    name = re.sub(r'[\s\-]+$', '', name)
    
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    if len(name) < 2:
        return None
    
    return name


def test_parser():
    """Test function to validate parser."""
    test_cases = [
        # NEFT with suffix codes like BATC
        ("BY TRANSFER-NEFT*AUBL0002250*AUBLH15324467510*Vijay Kumar*BATC--", "Vijay Kumar"),
        ("BY TRANSFER-NEFT*BARB0CORAHM*BARBR25112062346*GHV INDIA PRIVAT--", "GHV INDIA PRIVAT"),
        ("BY TRANSFER-NEFT*BARB0BANSUG*BARBR25112062347*SHREE KRISHNA ENTERPRISES--", "SHREE KRISHNA ENTERPRISES"),
        ("BY TRANSFER-NEFT*HDFC0000240*HDFCH00535625057*APG INFOSOL LLP*--", "APG INFOSOL LLP"),
        ("BY TRANSFER-NEFT*HDFC0000001*HDFCH00618475241*APG INFOSOL LLP*--", "APG INFOSOL LLP"),
        ("BY TRANSFER-NEFT*SBIN0031254*SBINR25112062348*RAJESH KUMAR*--", "RAJESH KUMAR"),
        ("BY TRANSFER-NEFT*PUNB0123456*PUNBR25112062349*SURESH & CO--", "SURESH & CO"),
        
        # Standard formats
        ("DEBIT-CMP MANDATE DEBIT Bajaj Finance Ltd. - DD--", "Bajaj Finance Ltd."),
        ("CHEQUE WDL-CHEQUE TRANSFER TO--640918", None),
        ("CASH CHEQUE-CASH WITHDRAWAL BY CHQ--640919", "Cash"),
        ("BY TRANSFER-UPI/CR/968406802345/RAMSINGH/SBIN/9166769006/Payme--", "RAMSINGH"),
        ("CHEQUE DEPOSIT---370303", None),
        ("BY TRANSFER-CMP BAJAJ FINANCE LTD--", "BAJAJ FINANCE LTD"),
        ("TO TRANSFER-UPI/DR/003757576619/MAHAVIR /SBIN/9314093111/Payme--", "MAHAVIR"),
        ("DEBIT-ATMCard AMC 521782*1844--", "Bank Charges"),
        ("BY TRANSFER-NEFT*AUBL0002011*AUBLH27523144089*SHAILENDRA KRIPL--", "SHAILENDRA KRIPL"),
        ("CHQ TRANSFER-NEFT UTR NO: SBIN325287801513--676210 GANDHAR UDYOG", "GANDHAR UDYOG"),
        ("TO CLEARING-Chq 676216 Sess 6 T POWER TRANSFORMER A 0001002318--676216", "T POWER TRANSFORMER"),
        ("BY TRANSFER-RTGS UTR NO: BARBR22025071720270118--TIRUPATI STONE CRUSHER", "TIRUPATI STONE CRUSHER"),
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for narration, expected in test_cases:
        result = extract(narration)
        status = "PASS" if result == expected else "FAIL"
        
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        
        results.append({
            'narration': narration[:70],
            'expected': expected,
            'got': result,
            'status': status
        })
    
    return {
        'total': len(test_cases),
        'passed': passed,
        'failed': failed,
        'results': results
    }


if __name__ == "__main__":
    print("=" * 70)
    print("SBI Current Account Parser - Test Results")
    print("=" * 70)
    
    test_results = test_parser()
    
    for r in test_results['results']:
        status_symbol = "✓" if r['status'] == "PASS" else "✗"
        print(f"{status_symbol} {r['narration'][:60]:<60}")
        print(f"   Expected: {str(r['expected']):<30} | Got: {str(r['got'])}")
    
    print("-" * 70)
    print(f"Total: {test_results['total']} | Passed: {test_results['passed']} | Failed: {test_results['failed']}")