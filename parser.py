# engine/parser.py
"""
Bank statement file parser.
Handles SBI bank statement format with metadata header.
"""

import pandas as pd
import os
import re


def load_statement(filepath):
    """
    Loads a bank statement (CSV or Excel) into a pandas DataFrame.
    Handles SBI format with metadata rows before transaction data.
    """
    try:
        print(f"\n=== Loading Statement: {filepath} ===")
        
        # Read the Excel file without header
        df_raw = pd.read_excel(filepath, header=None, dtype=str)
        
        print(f"Raw shape: {df_raw.shape}")
        print(f"\nScanning all rows for transaction data...")
        
        # Find where the actual transaction data starts
        header_row_idx = None
        
        for i in range(len(df_raw)):
            row = df_raw.iloc[i]
            row_values = [str(v).strip() if pd.notna(v) else '' for v in row.tolist()]
            row_text = ' '.join(row_values).upper()
            
            # Check if this row contains transaction headers
            has_date = 'DATE' in row_text
            has_narration = any(kw in row_text for kw in ['NARRATION', 'DESCRIPTION', 'PARTICULARS'])
            has_debit = 'DEBIT' in row_text
            has_credit = 'CREDIT' in row_text
            
            header_score = sum([has_date, has_narration, has_debit, has_credit])
            
            if header_score >= 2:
                print(f"\nRow {i}: Found header row (score: {header_score})")
                print(f"  Values: {row_values[:8]}")
                header_row_idx = i
                break
        
        if header_row_idx is None:
            print("ERROR: Could not find header row!")
            return None, "Could not find transaction header row in the file"
        
        # Read the data starting from the header row
        df = pd.read_excel(filepath, skiprows=header_row_idx, dtype=str)
        
        print(f"\nColumns found: {df.columns.tolist()}")
        print(f"Shape: {df.shape}")
        print(f"\nFirst 5 rows:")
        print(df.head())
        
        # Map columns to standard names
        df = _map_columns(df)
        
        # Ensure required columns exist
        df = _ensure_columns(df)
        
        # Clean the data
        df = _clean_data(df)
        
        print(f"\n=== Final Result ===")
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"\nFirst 5 rows:")
        print(df.head())
        
        return df, None
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return None, str(e)


def _map_columns(df):
    """Map columns to standard names based on content."""
    
    print(f"\n=== Mapping Columns ===")
    
    if len(df) == 0:
        return df
    
    original_cols = df.columns.tolist()
    print(f"Original columns: {original_cols}")
    
    # Create mapping - only map FIRST match for each type
    col_mapping = {}
    mapped_targets = set()
    
    for col in original_cols:
        col_upper = str(col).upper().strip()
        
        # DATE - only map first date column
        if 'DATE' not in mapped_targets:
            if any(kw in col_upper for kw in ['TXN DATE', 'TRANSACTION DATE', 'DATE']):
                col_mapping[col] = 'DATE'
                mapped_targets.add('DATE')
                print(f"  '{col}' -> DATE")
                continue
        
        # Skip second date column (Value Date)
        if any(kw in col_upper for kw in ['VALUE DATE', 'VAL DATE']):
            print(f"  '{col}' -> Skipped (duplicate date)")
            continue
        
        # DESCRIPTION
        if 'DESCRIPTION' not in mapped_targets:
            if any(kw in col_upper for kw in ['NARRATION', 'DESCRIPTION', 'PARTICULARS', 'DESC', 'REMARKS', 'DETAILS']):
                col_mapping[col] = 'DESCRIPTION'
                mapped_targets.add('DESCRIPTION')
                print(f"  '{col}' -> DESCRIPTION")
                continue
        
        # REFERENCE
        if 'REFERENCE' not in mapped_targets:
            if any(kw in col_upper for kw in ['REFERENCE', 'REF', 'CHEQUE', 'CHQ', 'INST', 'CHEQ']):
                col_mapping[col] = 'REFERENCE'
                mapped_targets.add('REFERENCE')
                print(f"  '{col}' -> REFERENCE")
                continue
        
        # DEBIT
        if 'DEBIT' not in mapped_targets:
            if any(kw in col_upper for kw in ['DEBIT', 'WITHDRAWAL', 'DR']) and 'CREDIT' not in col_upper:
                col_mapping[col] = 'DEBIT'
                mapped_targets.add('DEBIT')
                print(f"  '{col}' -> DEBIT")
                continue
        
        # CREDIT
        if 'CREDIT' not in mapped_targets:
            if any(kw in col_upper for kw in ['CREDIT', 'DEPOSIT', 'CR']) and 'DEBIT' not in col_upper:
                col_mapping[col] = 'CREDIT'
                mapped_targets.add('CREDIT')
                print(f"  '{col}' -> CREDIT")
                continue
        
        # BALANCE
        if 'BALANCE' not in mapped_targets:
            if any(kw in col_upper for kw in ['BALANCE', 'BAL', 'CLOSING BAL']):
                col_mapping[col] = 'BALANCE'
                mapped_targets.add('BALANCE')
                print(f"  '{col}' -> BALANCE")
                continue
        
        # Skip Branch Code and other columns
        print(f"  '{col}' -> Skipped")
    
    print(f"\nColumn mapping: {col_mapping}")
    
    # Apply mapping
    df = df.rename(columns=col_mapping)
    
    # Keep only the mapped columns
    keep_cols = [c for c in df.columns if c in ['DATE', 'DESCRIPTION', 'DEBIT', 'CREDIT', 'BALANCE', 'REFERENCE']]
    df = df[keep_cols]
    
    print(f"Final columns: {df.columns.tolist()}")
    
    return df


def _ensure_columns(df):
    """Ensure all required columns exist."""
    
    defaults = {
        'DATE': '',
        'DESCRIPTION': '',
        'DEBIT': 0,
        'CREDIT': 0,
        'BALANCE': 0,
        'REFERENCE': ''
    }
    
    for col, default in defaults.items():
        if col not in df.columns:
            print(f"Creating missing column: {col}")
            df[col] = default
    
    return df


def _clean_data(df):
    """Clean the dataframe."""
    
    print(f"\n=== Cleaning Data ===")
    print(f"Rows before cleaning: {len(df)}")
    
    # Check if we have proper columns
    print(f"Columns: {df.columns.tolist()}")
    print(f"Column types: {df.dtypes.to_dict()}")
    
    # Clean DATE column
    if 'DATE' in df.columns:
        print(f"DATE column type: {type(df['DATE'])}")
        
        # If DATE is a DataFrame (duplicate columns), take the first one
        if isinstance(df['DATE'], pd.DataFrame):
            print("WARNING: DATE has duplicate columns, taking first")
            df['DATE'] = df['DATE'].iloc[:, 0]
        
        df['DATE'] = df['DATE'].astype(str)
        df['DATE'] = df['DATE'].str.strip()
        df['DATE'] = df['DATE'].replace(['nan', 'None', 'NaT', '<NA>'], '')
        
        # Remove time component if present
        df['DATE'] = df['DATE'].str.split(' ').str[0]
        
        print(f"Sample dates: {df['DATE'].head().tolist()}")
    
    # Clean numeric columns
    for col in ['DEBIT', 'CREDIT', 'BALANCE']:
        if col in df.columns:
            # Check if column is DataFrame (duplicate)
            if isinstance(df[col], pd.DataFrame):
                print(f"WARNING: {col} has duplicate columns, taking first")
                df[col] = df[col].iloc[:, 0]
            
            df[col] = df[col].fillna('0')
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(['', 'nan', 'None', 'NaT', '<NA>'], '0')
            df[col] = df[col].str.replace(',', '', regex=False)
            df[col] = df[col].str.replace(r'[^\d.-]', '', regex=True)
            df[col] = df[col].replace('', '0')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Clean text columns
    for col in ['DESCRIPTION', 'REFERENCE']:
        if col in df.columns:
            if isinstance(df[col], pd.DataFrame):
                print(f"WARNING: {col} has duplicate columns, taking first")
                df[col] = df[col].iloc[:, 0]
            
            df[col] = df[col].fillna('')
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(['nan', 'None', 'NaT', '<NA>'], '')
    
    # Remove empty rows
    before = len(df)
    df = df[~((df['DEBIT'] == 0) & (df['CREDIT'] == 0) & 
             (df['DESCRIPTION'] == '') & (df['DATE'] == ''))]
    
    print(f"Removed {before - len(df)} empty rows")
    print(f"Rows after cleaning: {len(df)}")
    
    # Reset index
    df = df.reset_index(drop=True)
    
    return df