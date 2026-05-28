# main.py
"""
Bank Statement to Tally Integrator
Main application with screen orchestration.

Workflow:
1. Select Bank → Upload Bank Statement → Upload Tally Master XML (Optional) → Upload Daybook XML (Optional)
2. Review Extraction (Correct extracted names)
3. Name Confirmation (Group similar names)
4. Account Review (View transactions per account)
5a. New Company: Map to default groups (Sundry Debtors/Creditors)
5b. Existing Company: Map to existing Tally Masters
6. Duplicate Check (if Daybook uploaded)
7. Final Review & Generate XML
"""

import sys
import traceback
import customtkinter as ctk
import tkinter.filedialog as fd
import os

from engine.tally_parser import TallyMasterParser
from engine.parser import load_statement
from engine.extractor import extract_account_info
from engine.matcher import group_similar_names
from engine.parser_manager import get_parser_manager


# Theme setup
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Main application class"""
    
    def __init__(self):
        super().__init__()

        self.title("Bank Statement to Tally Integrator")
        self.geometry("1000x750")
        self.minsize(900, 650)

        # Data storage
        self.bank_statement_df = None
        self.bank_id = None
        self.tally_ledgers = []
        self.tally_vouchers = []
        self.tally_ledger_names = []
        self.grouped_names = []
        self.confirmed_primary_names = []
        self.name_aliases = {}
        self.final_mappings = {}
        self.new_ledgers_to_create = []
        self.ledger_groups = {}
        self.final_transactions = []
        self.tally_xml_uploaded = False
        self.daybook_xml_uploaded = False
        self.company_name = ""

        # Screen references
        self.current_screen = None

        # Grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._create_sidebar()
        self._create_main_frame()
        
        self._log("=" * 50)
        self._log("Bank Statement to Tally Integrator")
        self._log("=" * 50)
        self._log("")
        self._log("Getting Started:")
        self._log("1. Select your bank from the dropdown")
        self._log("2. Upload your bank statement (Excel/CSV)")
        self._log("3. Optionally upload Tally Master XML")
        self._log("4. Optionally upload Daybook XML")
        self._log("5. Click 'Start Processing'")
        self._log("")
    
    def _log(self, message):
        """Add message to log box"""
        if hasattr(self, 'log_box') and self.log_box is not None:
            try:
                self.log_box.configure(state="normal")
                self.log_box.insert("end", message + "\n")
                self.log_box.configure(state="disabled")
                self.log_box.see("end")
            except:
                pass
    
    def _create_sidebar(self):
        """Create sidebar with controls"""
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(16, weight=1)

        # Title
        ctk.CTkLabel(
            self.sidebar_frame, 
            text="Tally Integrator", 
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 5))
        
        ctk.CTkLabel(
            self.sidebar_frame, 
            text="v1.0 - Tally.ERP 9", 
            font=ctk.CTkFont(size=10), 
            text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 10))

        # Bank Selection
        ctk.CTkLabel(self.sidebar_frame, text="Select Bank:*", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, padx=20, pady=(10, 5), sticky="w")
        
        parser_manager = get_parser_manager()
        banks = parser_manager.get_all_banks()
        bank_names = [b['name'] for b in banks]
        bank_ids = [b['id'] for b in banks]
        
        self.bank_names = bank_names
        self.bank_ids = bank_ids
        
        self.bank_dropdown = ctk.CTkComboBox(
            self.sidebar_frame, 
            values=bank_names if bank_names else ["No banks available"],
            width=240
        )
        self.bank_dropdown.grid(row=3, column=0, padx=20, pady=(0, 15))
        
        if bank_names:
            self.bank_dropdown.set(bank_names[0])
        
        ctk.CTkButton(
            self.sidebar_frame,
            text="Manage Parsers",
            fg_color="gray",
            width=240,
            command=self._show_manage_parsers
        ).grid(row=4, column=0, padx=20, pady=(0, 15))

        # Bank Statement Upload
        ctk.CTkLabel(self.sidebar_frame, text="Bank Statement:*", font=ctk.CTkFont(weight="bold")).grid(
            row=5, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.bank_file_path_var = ctk.StringVar(value="No file selected")
        ctk.CTkButton(
            self.sidebar_frame, 
            text="Upload Bank Statement", 
            width=240,
            command=self._upload_bank_statement
        ).grid(row=6, column=0, padx=20, pady=5)
        
        ctk.CTkLabel(
            self.sidebar_frame, 
            textvariable=self.bank_file_path_var, 
            font=ctk.CTkFont(size=10), 
            text_color="gray",
            wraplength=240
        ).grid(row=7, column=0, padx=20)

        # Tally Master XML Upload
        ctk.CTkLabel(
            self.sidebar_frame, 
            text="Tally Master XML (Optional):",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=8, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.tally_file_path_var = ctk.StringVar(value="No file selected")
        ctk.CTkButton(
            self.sidebar_frame, 
            text="Upload Tally Master XML", 
            width=240,
            fg_color="#4CAF50",
            command=self._upload_tally_master
        ).grid(row=9, column=0, padx=20, pady=5)
        
        ctk.CTkLabel(
            self.sidebar_frame, 
            textvariable=self.tally_file_path_var, 
            font=ctk.CTkFont(size=10), 
            text_color="gray",
            wraplength=240
        ).grid(row=10, column=0, padx=20)

        # Daybook XML Upload
        ctk.CTkLabel(
            self.sidebar_frame, 
            text="Daybook XML (Optional):",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=11, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.daybook_file_path_var = ctk.StringVar(value="No file selected")
        ctk.CTkButton(
            self.sidebar_frame, 
            text="Upload Daybook XML", 
            width=240,
            fg_color="#2196F3",
            command=self._upload_daybook
        ).grid(row=12, column=0, padx=20, pady=5)
        
        ctk.CTkLabel(
            self.sidebar_frame, 
            textvariable=self.daybook_file_path_var, 
            font=ctk.CTkFont(size=10), 
            text_color="gray",
            wraplength=240
        ).grid(row=13, column=0, padx=20)

        # Status
        self.tally_status_var = ctk.StringVar(value="No Tally XML uploaded")
        ctk.CTkLabel(
            self.sidebar_frame, 
            textvariable=self.tally_status_var, 
            font=ctk.CTkFont(size=10), 
            text_color="gray"
        ).grid(row=14, column=0, padx=20, pady=5)
        
        self.company_label_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            self.sidebar_frame, 
            textvariable=self.company_label_var, 
            font=ctk.CTkFont(size=10), 
            text_color="#4CAF50"
        ).grid(row=15, column=0, padx=20, pady=(0, 10), sticky="nw")

        # Process Button
        self.process_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="Start Processing", 
            fg_color="green", 
            hover_color="darkgreen",
            width=240,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._process_data
        )
        self.process_btn.grid(row=16, column=0, padx=20, pady=20)

    def _create_main_frame(self):
        """Create main content area"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(self.main_frame, state="disabled", font=ctk.CTkFont(size=11))
        self.log_box.grid(row=0, column=0, sticky="nsew")

    def _clear_main_frame(self):
        """Clear main frame for new screen"""
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()

    def _show_screen(self, screen_class, *args, **kwargs):
        """Show a screen in main frame"""
        self._clear_main_frame()
        
        if screen_class is None:
            self.log_box.grid(row=0, column=0, sticky="nsew")
            return
        
        self.current_screen = screen_class(self.main_frame, *args, **kwargs)
        self.current_screen.grid(row=0, column=0, sticky="nsew")
    
    def _show_manage_parsers(self):
        """Show manage parsers screen"""
        from ui.manage_parsers_screen import ManageParsersScreen
        self._show_screen(ManageParsersScreen, on_back=self._return_to_main)
    
    def _return_to_main(self):
        """Return to main screen"""
        self._clear_main_frame()
        self.log_box.grid(row=0, column=0, sticky="nsew")
        self.current_screen = None
    
    def _upload_bank_statement(self):
        """Handle bank statement file upload"""
        filename = fd.askopenfilename(
            title="Select Bank Statement",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.bank_file_path_var.set(os.path.basename(filename))
            self.bank_file_full_path = filename
            self._log(f"Bank Statement: {os.path.basename(filename)}")

    def _upload_tally_master(self):
        """Handle Tally Master XML file upload"""
        filename = fd.askopenfilename(
            title="Select Tally Master XML",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.tally_file_path_var.set(os.path.basename(filename))
            self.tally_file_full_path = filename
            self.tally_xml_uploaded = True
            
            parser = TallyMasterParser()
            result = parser.parse_master_xml(filename)
            
            if result['success']:
                self.tally_ledgers = result['ledgers']
                self.tally_vouchers = result['vouchers']
                self.tally_ledger_names = parser.get_ledger_names()
                self.company_name = result.get('company_name', 'Company')
                
                self.tally_status_var.set(f"{len(self.tally_ledgers)} ledgers loaded")
                self.company_label_var.set(f"Company: {self.company_name[:30]}")
                self._log(f"Tally XML loaded: {len(self.tally_ledgers)} ledgers")
                self._log(f"Vouchers loaded: {len(self.tally_vouchers)}")
            else:
                self._log(f"ERROR: {result['error']}")
                self.tally_xml_uploaded = False

    def _upload_daybook(self):
        """Handle Daybook XML file upload"""
        filename = fd.askopenfilename(
            title="Select Daybook XML",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.daybook_file_path_var.set(os.path.basename(filename))
            self.daybook_file_full_path = filename
            self.daybook_xml_uploaded = True
            
            parser = TallyMasterParser()
            result = parser.parse_master_xml(filename)
            
            if result['success']:
                self.tally_vouchers.extend(result['vouchers'])
                self._log(f"Daybook XML loaded: {len(result['vouchers'])} vouchers")
            else:
                self._log(f"ERROR: {result['error']}")
                self.daybook_xml_uploaded = False

    def _process_data(self):
        """Main processing function"""
        bank_name = self.bank_dropdown.get()
        bank_index = self.bank_names.index(bank_name) if bank_name in self.bank_names else -1
        
        if bank_index < 0:
            self._log("ERROR: Please select a valid bank.")
            return
        
        self.bank_id = self.bank_ids[bank_index]
        
        if not hasattr(self, 'bank_file_full_path'):
            self._log("ERROR: Please upload bank statement.")
            return
        
        self._log("")
        self._log("=" * 50)
        self._log(f"PROCESSING: {bank_name}")
        self._log("=" * 50)
        self._log("")
        self._log("[Step 1] Loading Bank Statement...")
        
        df, err = load_statement(self.bank_file_full_path)
        if err:
            self._log(f"ERROR: {err}")
            return
        
        self.bank_statement_df = df
        
        self._log(f"Loaded {len(df)} transactions.")
        self._log(f"Columns: {df.columns.tolist()}")
        
        if 'DATE' in df.columns:
            self._log(f"DATE column found")
            self._log(f"Sample dates: {df['DATE'].head().tolist()}")
            non_empty = (df['DATE'] != '').sum()
            self._log(f"Non-empty dates: {non_empty}/{len(df)}")
        else:
            self._log(f"WARNING: No DATE column found in dataframe!")
        
        self._log("")
        self._log("[Step 2] Extracting Account Names...")
        
        df['EXTRACTED_INFO'] = df['DESCRIPTION'].apply(
            lambda x: extract_account_info(str(x), self.bank_id)
        )
        df['EXTRACTED_NAME'] = df['EXTRACTED_INFO'].apply(lambda x: x['extracted_name'])
        
        def determine_type(row):
            debit = float(row.get('DEBIT', 0) or 0)
            credit = float(row.get('CREDIT', 0) or 0)
            if credit > 0 and debit == 0:
                return 'Receipt'
            elif debit > 0 and credit == 0:
                return 'Payment'
            elif credit >= debit:
                return 'Receipt'
            else:
                return 'Payment'
        
        df['TRANS_TYPE'] = df.apply(determine_type, axis=1)
        
        def set_fallback(row):
            extracted = row.get('EXTRACTED_NAME')
            if extracted and str(extracted) not in ['None', '', 'nan']:
                return extracted
            trans_type = row.get('TRANS_TYPE', 'Payment')
            return 'Payment made' if trans_type == 'Payment' else 'Payment Receipt'
        
        df['FINAL_NAME'] = df.apply(set_fallback, axis=1)
        
        review_count = sum(1 for _, row in df.iterrows() if row.get('EXTRACTED_INFO', {}).get('needs_review', False))
        
        self._log(f"Extracted names from {len(df)} transactions")
        self._log(f"  - Need review: {review_count}")
        self._log(f"  - Auto-extracted: {len(df) - review_count}")
        
        self._log("")
        self._log("[Step 3] Review Extraction...")
        self.after(500, self._show_review_extraction_screen)
    
    def _show_review_extraction_screen(self):
        """Show review extraction screen"""
        from ui.review_extraction_screen import ReviewExtractionScreen
        self._show_screen(
            ReviewExtractionScreen,
            self.bank_statement_df,
            self._on_review_extraction_complete
        )
    
    def _on_review_extraction_complete(self, corrected_df, go_back):
        """After review extraction"""
        if go_back:
            self._return_to_main()
            return
        
        if corrected_df is not None:
            self.bank_statement_df = corrected_df
        
        self._log("Review complete. Corrections applied.")
        self._proceed_to_name_confirmation()
    
    def _proceed_to_name_confirmation(self):
        """Prepare and show name confirmation screen"""
        df = self.bank_statement_df
        
        unique_names = df['FINAL_NAME'].unique().tolist()
        unique_names = [n for n in unique_names if str(n) not in ['None', 'nan', '']]
        
        self._log(f"\n[Step 4] Grouping {len(unique_names)} unique names...")
        self.grouped_names = group_similar_names(unique_names, threshold=85)
        
        groups_needing_conf = len([g for g in self.grouped_names if len(g) > 1])
        auto_confirmed = len([g for g in self.grouped_names if len(g) == 1])
        
        self._log(f"Groups found: {len(self.grouped_names)}")
        self._log(f"  - Auto-confirmed: {auto_confirmed}")
        self._log(f"  - Need confirmation: {groups_needing_conf}")
        
        self._show_name_confirmation_screen()
    
    def _show_name_confirmation_screen(self):
        """Show name confirmation screen"""
        from ui.name_confirmation_screen import NameConfirmationScreen
        self._show_screen(
            NameConfirmationScreen,
            self.grouped_names,
            self._on_name_confirmation_complete
        )
    
    def _on_name_confirmation_complete(self, confirmed_groups, name_aliases):
        """After name confirmation"""
        if confirmed_groups is None and name_aliases is None:
            self._show_review_extraction_screen()
            return
        
        self.confirmed_primary_names = confirmed_groups
        self.name_aliases = name_aliases
        
        self._log(f"Name confirmation complete: {len(confirmed_groups)} accounts, {len(name_aliases)} aliases")
        self._show_account_review_screen()
    
    def _show_account_review_screen(self):
        """Show account review screen"""
        from ui.account_review_screen import SimpleAccountReviewScreen
        self._show_screen(
            SimpleAccountReviewScreen,
            self.confirmed_primary_names,
            self.name_aliases,
            self.bank_statement_df,
            self._on_account_review_complete
        )
    
    def _on_account_review_complete(self, final_names, updated_aliases, name_changes, go_back):
        """After account review"""
        if go_back:
            self._show_name_confirmation_screen()
            return
        
        if final_names:
            self.confirmed_primary_names = final_names
        if updated_aliases:
            self.name_aliases = updated_aliases
        
        self._log(f"Account review complete: {len(self.confirmed_primary_names)} accounts")
        
        # Route to appropriate mapping screen based on whether Tally XML was uploaded
        if self.tally_xml_uploaded:
            self._show_tally_mapping_screen()
        else:
            self._show_new_company_screen()
    
    def _show_new_company_screen(self):
        """Show new company fast setup screen (no Tally Master XML uploaded)"""
        from ui.new_company_fast_screen import NewCompanyFastScreen
        self._show_screen(
            NewCompanyFastScreen,
            self.confirmed_primary_names,
            [],
            self._on_new_company_complete
        )
    
    def _on_new_company_complete(self, final_mappings, new_ledgers, ledger_groups, go_back):
        """After new company setup"""
        if go_back:
            self._show_account_review_screen()
            return
        
        self.final_mappings = final_mappings
        self.new_ledgers_to_create = new_ledgers if new_ledgers else []
        self.ledger_groups = ledger_groups if ledger_groups else {}
        
        self._log(f"New company setup complete: {len(final_mappings)} accounts")
        self._show_final_review_screen(is_existing_company=False)
    
    def _show_tally_mapping_screen(self):
        """Show Tally mapping screen (Tally Master XML uploaded)"""
        from ui.tally_mapping_screen import TallyMappingScreen
        self._show_screen(
            TallyMappingScreen,
            self.confirmed_primary_names,
            self.tally_ledger_names,
            self._on_tally_mapping_complete
        )
    
    def _on_tally_mapping_complete(self, final_mappings, new_ledgers, ledger_groups, go_back):
        """After Tally mapping"""
        if go_back:
            self._show_account_review_screen()
            return
        
        self.final_mappings = final_mappings
        self.new_ledgers_to_create = new_ledgers if new_ledgers else []
        self.ledger_groups = ledger_groups if ledger_groups else {}
        
        self._log(f"Tally mapping complete: {len(final_mappings)} accounts mapped")
        self._show_final_review_screen(is_existing_company=True)
    
    def _show_final_review_screen(self, is_existing_company=False):
        """Show final review screen - prepares transactions then shows review"""
        self._log(f"\n[Step 6] Preparing transactions...")
        
        # Prepare transactions
        transactions = self._prepare_transactions_data()
        
        if not transactions:
            self._log("ERROR: No transactions to process!")
            return
        
        self.final_transactions = transactions
        
        self._log(f"Prepared {len(transactions)} transactions")
        
        # Check if Daybook XML was uploaded for duplicate checking
        if self.daybook_xml_uploaded and self.tally_vouchers:
            self._show_duplicate_check_screen()
        else:
            # Show final review screen
            from ui.review_screen import ReviewScreen
            self._show_screen(
                ReviewScreen,
                self.final_transactions,
                self.new_ledgers_to_create,
                self.ledger_groups,
                self._on_final_review_complete,
                company_name=self.company_name,
                is_existing_company=is_existing_company
            )
    
    def _prepare_transactions_data(self):
        """Prepare transaction list with proper date handling"""
        transactions = []
        
        if self.bank_statement_df is None or self.bank_statement_df.empty:
            self._log("ERROR: bank_statement_df is None or empty!")
            return transactions
        
        has_date = 'DATE' in self.bank_statement_df.columns
        
        for idx, row in self.bank_statement_df.iterrows():
            try:
                extracted_name = row.get('EXTRACTED_NAME', '')
                final_name = row.get('FINAL_NAME', '')
                
                name_to_use = final_name if final_name else extracted_name
                
                # Resolve aliases
                primary_name = None
                if name_to_use in self.name_aliases:
                    primary_name = self.name_aliases[name_to_use]
                elif extracted_name in self.name_aliases:
                    primary_name = self.name_aliases[extracted_name]
                else:
                    primary_name = name_to_use
                
                if not primary_name or str(primary_name).strip() == '':
                    continue
                
                if str(primary_name).upper() in ['UNKNOWN', 'NONE', 'NAN']:
                    continue
                
                # Get mapped ledger
                mapped_ledger = self.final_mappings.get(primary_name, primary_name)
                
                # Get amounts
                credit = float(row.get('CREDIT', 0) or 0)
                debit = float(row.get('DEBIT', 0) or 0)
                
                if credit > 0:
                    amount = credit
                    trans_type = 'Receipt'
                elif debit > 0:
                    amount = debit
                    trans_type = 'Payment'
                else:
                    continue
                
                # GET DATE
                date_val = ''
                try:
                    if has_date:
                        raw_date = row.get('DATE', '')
                        date_val = str(raw_date) if raw_date else ''
                        date_val = date_val.strip()
                        if date_val.endswith('.0'):
                            date_val = date_val[:-2]
                        if date_val.lower() in ['nan', 'none', '']:
                            date_val = ''
                except:
                    date_val = ''
                
                narration = str(row.get('DESCRIPTION', ''))
                reference = str(row.get('REFERENCE', ''))
                
                transactions.append({
                    'date': date_val,
                    'amount': amount,
                    'narration': narration,
                    'reference': reference,
                    'type': trans_type,
                    'extracted_name': extracted_name,
                    'mapped_ledger': mapped_ledger
                })
                
            except Exception as e:
                print(f"Error processing row {idx}: {e}")
                continue
        
        # Sort by date (oldest first)
        transactions.sort(key=lambda x: x.get('date', ''))
        
        return transactions
    
    def _show_duplicate_check_screen(self):
        """Show duplicate check screen"""
        from ui.duplicate_check_screen import DuplicateCheckScreen
        self._show_screen(
            DuplicateCheckScreen,
            self.final_transactions,
            self.tally_vouchers,
            self._on_duplicate_check_complete
        )
    
    def _on_duplicate_check_complete(self, filtered_transactions):
        """After duplicate check"""
        if filtered_transactions is None:
            if self.tally_xml_uploaded:
                self._show_tally_mapping_screen()
            else:
                self._show_new_company_screen()
            return
        
        original_count = len(self.final_transactions)
        self.final_transactions = filtered_transactions
        skipped = original_count - len(filtered_transactions)
        
        self._log(f"Duplicate check complete: {skipped} skipped, {len(filtered_transactions)} to import")
        
        # Show final review
        is_existing = self.tally_xml_uploaded
        from ui.review_screen import ReviewScreen
        self._show_screen(
            ReviewScreen,
            self.final_transactions,
            self.new_ledgers_to_create,
            self.ledger_groups,
            self._on_final_review_complete,
            company_name=self.company_name,
            is_existing_company=is_existing
        )
    
    def _on_final_review_complete(self, result):
        """After final review"""
        self._return_to_main()
        
        if result is None:
            if self.daybook_xml_uploaded:
                self._show_duplicate_check_screen()
            elif self.tally_xml_uploaded:
                self._show_tally_mapping_screen()
            else:
                self._show_new_company_screen()
        else:
            self._log("")
            self._log("=" * 50)
            self._log("PROCESS COMPLETE!")
            self._log("=" * 50)


def main():
    """Main entry point"""
    try:
        app = App()
        app.mainloop()
        
    except ImportError as e:
        print(f"ERROR: Missing module - {e}")
        print("\nInstall required packages:")
        print("pip install customtkinter pandas thefuzz openpyxl")
        try:
            input("\nPress Enter to exit...")
        except:
            pass
        
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        try:
            input("\nPress Enter to exit...")
        except:
            pass


if __name__ == "__main__":
    main()