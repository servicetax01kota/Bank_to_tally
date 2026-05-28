# ui/review_screen.py
"""
Final Review Screen - Generate XML files for Tally import.
"""

import customtkinter as ctk
from typing import List, Dict
import tkinter.filedialog as fd
import os


class ReviewScreen(ctk.CTkFrame):
    """
    Final review - Generate XML files.
    Works for both New Company and Existing Company workflows.
    """
    
    def __init__(self, master, transactions: List[Dict], new_ledgers: List[str], 
                 ledger_groups: Dict[str, str], on_complete, company_name="",
                 is_existing_company=False):
        super().__init__(master)
        
        self.transactions = transactions if transactions else []
        self.new_ledgers = new_ledgers if new_ledgers else []
        self.ledger_groups = ledger_groups if ledger_groups else {}
        self.on_complete_callback = on_complete
        self.company_name = company_name
        self.is_existing_company = is_existing_company
        
        self._create_ui()
    
    def _create_ui(self):
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title = "Review and Generate XML Files"
        if self.is_existing_company:
            title = "Review and Generate XML Files (Existing Company)"
        
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, pady=20, padx=20, sticky="w")
        
        # Bank name input (more prominent)
        bank_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        bank_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            bank_frame,
            text="Bank Account Name in Tally:*",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=20, pady=10)
        
        self.bank_name_var = ctk.StringVar(value="Bank Account")
        
        # Try to get bank name from Tally masters if available
        if self.is_existing_company:
            # Look for common bank account names in ledger groups
            for ledger, group in self.ledger_groups.items():
                if 'BANK' in group.upper():
                    self.bank_name_var.set(ledger)
                    break
        
        bank_entry = ctk.CTkEntry(
            bank_frame,
            textvariable=self.bank_name_var,
            width=300,
            font=ctk.CTkFont(size=12)
        )
        bank_entry.pack(side="left", padx=10, pady=10)
        
        ctk.CTkLabel(
            bank_frame,
            text="(Enter the exact name of your bank ledger in Tally)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(side="left", padx=10, pady=10)
        
        # Summary cards
        summary_frame = ctk.CTkFrame(self)
        summary_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # Masters card
        masters_card = ctk.CTkFrame(summary_frame, fg_color=("gray80", "gray20"), corner_radius=10)
        masters_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            masters_card,
            text="MASTERS XML",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            masters_card,
            text=str(len(self.new_ledgers)),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#4CAF50"
        ).pack()
        
        label_text = "New Ledgers" if self.new_ledgers else "No New Ledgers"
        ctk.CTkLabel(
            masters_card,
            text=label_text,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=(0, 15))
        
        # Show new ledgers if any
        if self.new_ledgers:
            ledgers_text = ", ".join(self.new_ledgers[:5])
            if len(self.new_ledgers) > 5:
                ledgers_text += f"... (+{len(self.new_ledgers) - 5} more)"
            ctk.CTkLabel(
                masters_card,
                text=ledgers_text,
                font=ctk.CTkFont(size=9),
                text_color="gray",
                wraplength=200
            ).pack(pady=(0, 10))
        
        # Vouchers card
        vouchers_card = ctk.CTkFrame(summary_frame, fg_color=("gray80", "gray20"), corner_radius=10)
        vouchers_card.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            vouchers_card,
            text="VOUCHERS XML",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2196F3"
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            vouchers_card,
            text=str(len(self.transactions)),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#2196F3"
        ).pack()
        
        ctk.CTkLabel(
            vouchers_card,
            text="Transactions",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=(0, 15))
        
        # Transaction type breakdown
        receipt_count = sum(1 for t in self.transactions if t.get('type') == 'Receipt')
        payment_count = sum(1 for t in self.transactions if t.get('type') == 'Payment')
        contra_count = sum(1 for t in self.transactions if 'CASH' in str(t.get('mapped_ledger', '')).upper())
        
        ctk.CTkLabel(vouchers_card, text=f"Receipts: {receipt_count}", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=20)
        ctk.CTkLabel(vouchers_card, text=f"Payments: {payment_count}", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=20)
        if contra_count > 0:
            ctk.CTkLabel(vouchers_card, text=f"Contra: {contra_count}", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=20)
        
        # Sample transactions
        sample_frame = ctk.CTkScrollableFrame(self, height=200)
        sample_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        
        ctk.CTkLabel(sample_frame, text="Sample Transactions:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=5)
        
        # Header row
        header_row = ctk.CTkFrame(sample_frame, fg_color=("gray70", "gray30"))
        header_row.pack(fill="x", pady=2)
        
        ctk.CTkLabel(header_row, text="Date", width=90, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Ledger", width=130, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Type", width=70, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Amount", width=100, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=5)
        
        for trans in self.transactions[:15]:
            row = ctk.CTkFrame(sample_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            
            date_str = str(trans.get('date', ''))[:10] if trans.get('date') else '-'
            ledger = str(trans.get('mapped_ledger', ''))[:20]
            trans_type = trans.get('type', '-')
            amount = f"₹{trans.get('amount', 0):,.2f}"
            
            ctk.CTkLabel(row, text=date_str, width=90, font=ctk.CTkFont(size=10), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=ledger, width=130, font=ctk.CTkFont(size=10), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=trans_type, width=70, font=ctk.CTkFont(size=10)).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=amount, width=100, font=ctk.CTkFont(size=10), anchor="e").pack(side="left", padx=5)
        
        if len(self.transactions) > 15:
            ctk.CTkLabel(
                sample_frame,
                text=f"... and {len(self.transactions) - 15} more transactions",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(anchor="w", pady=5)
        
        # Info
        info_frame = ctk.CTkFrame(self, fg_color=("#e3f2fd", "#1a237e"))
        info_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        if self.is_existing_company:
            info_text = (
                "📁 Files to be generated:\n"
                "1. Masters_XML.xml - New ledgers that don't exist in Tally\n"
                "2. Vouchers_XML.xml - Payment/Receipt entries mapped to existing Tally masters\n\n"
                "💡 Existing Tally masters will be used directly. Only new ledgers need to be created."
            )
        else:
            info_text = (
                "📁 Files to be generated:\n"
                "1. Masters_XML.xml - All new ledgers to create in Tally\n"
                "2. Vouchers_XML.xml - Payment/Receipt entries\n\n"
                "💡 Import Masters XML first, then Vouchers XML in Tally."
            )
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color=("#1565c0", "#90caf9"),
            justify="left"
        ).pack(pady=10, padx=20)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, padx=20, pady=15, sticky="ew")
        
        ctk.CTkButton(
            btn_frame, 
            text="← Back", 
            fg_color="gray", 
            command=self._go_back
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="Generate Masters Only", 
            fg_color="#4CAF50", 
            command=self._generate_masters_only
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="Generate Vouchers Only", 
            fg_color="#2196F3", 
            command=self._generate_vouchers_only
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="Generate Both", 
            fg_color="#FF9800",
            font=ctk.CTkFont(size=13, weight="bold"), 
            command=self._generate_both
        ).pack(side="right", padx=10)
    
    def _go_back(self):
        if self.on_complete_callback:
            self.on_complete_callback(None)

    def _generate_masters_only(self):
        """Generate only Masters XML"""
        if not self.new_ledgers:
            self._show_message("No New Ledgers", "There are no new ledgers to create.\nAll accounts are mapped to existing Tally masters.")
            return
        
        filepath = fd.asksaveasfilename(
            title="Save Masters XML", 
            defaultextension=".xml", 
            initialfile="Masters_XML.xml"
        )
        if not filepath:
            return
        
        if not filepath.endswith('.xml'):
            filepath += '.xml'
        
        try:
            from engine.xml_generator import TallyXMLGenerator
            generator = TallyXMLGenerator(
                company_name=self.company_name, 
                bank_ledger_name=self.bank_name_var.get()
            )
            result = generator.generate_masters_xml(
                self.new_ledgers, 
                self.ledger_groups, 
                filepath, 
                "9"
            )
            
            if result['success']:
                self._show_success(
                    "Success!", 
                    f"Masters XML created!\n{filepath}\n\nLedgers: {result.get('ledger_count', 0)}"
                )
            else:
                self._show_error("Error", result.get('error', 'Unknown error'))
        except Exception as e:
            self._show_error("Error", str(e))

    def _generate_vouchers_only(self):
        """Generate only Vouchers XML"""
        if not self.transactions:
            self._show_message("No Transactions", "There are no transactions to generate.")
            return
        
        filepath = fd.asksaveasfilename(
            title="Save Vouchers XML", 
            defaultextension=".xml", 
            initialfile="Vouchers_XML.xml"
        )
        if not filepath:
            return
        
        if not filepath.endswith('.xml'):
            filepath += '.xml'
        
        try:
            from engine.xml_generator import TallyXMLGenerator
            generator = TallyXMLGenerator(
                company_name=self.company_name, 
                bank_ledger_name=self.bank_name_var.get()
            )
            result = generator.generate_vouchers_xml(self.transactions, filepath)
            
            if result['success']:
                self._show_success(
                    "Success!", 
                    f"Vouchers XML created!\n{filepath}\n\nVouchers: {result.get('voucher_count', 0)}"
                )
            else:
                self._show_error("Error", result.get('error', 'Unknown error'))
        except Exception as e:
            self._show_error("Error", str(e))

    def _generate_both(self):
        """Generate both Masters and Vouchers XML"""
        if not self.transactions:
            self._show_message("No Transactions", "There are no transactions to generate.")
            return
        
        directory = fd.askdirectory(title="Select Folder for XML Files")
        if not directory:
            return
        
        from engine.xml_generator import TallyXMLGenerator
        generator = TallyXMLGenerator(
            company_name=self.company_name, 
            bank_ledger_name=self.bank_name_var.get()
        )
        
        results = []
        
        # Generate Masters if there are new ledgers
        if self.new_ledgers:
            masters_path = os.path.join(directory, "Masters_XML.xml")
            masters_result = generator.generate_masters_xml(
                self.new_ledgers, 
                self.ledger_groups, 
                masters_path, 
                "9"
            )
            results.append(f"Masters: {'✓' if masters_result['success'] else '✗'}")
        else:
            results.append("Masters: None (all mapped to existing)")
        
        # Generate Vouchers
        vouchers_path = os.path.join(directory, "Vouchers_XML.xml")
        vouchers_result = generator.generate_vouchers_xml(self.transactions, vouchers_path)
        results.append(f"Vouchers: {'✓' if vouchers_result['success'] else '✗'} ({vouchers_result.get('voucher_count', 0)})")
        
        success_msg = f"Files created in:\n{directory}\n\n" + "\n".join(results)
        self._show_success("Success!", success_msg)
    
    def _show_message(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("400x150")
        popup.grab_set()
        ctk.CTkLabel(popup, text=message).pack(expand=True, pady=20)
        ctk.CTkButton(popup, text="OK", command=popup.destroy).pack(pady=10)

    def _show_success(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("500x200")
        popup.grab_set()
        ctk.CTkLabel(
            popup, 
            text=message, 
            font=ctk.CTkFont(size=12), 
            wraplength=450, 
            justify="left",
            text_color="#4CAF50"
        ).pack(expand=True, pady=20)
        ctk.CTkButton(popup, text="OK", command=popup.destroy).pack(pady=10)

    def _show_error(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("500x250")
        popup.grab_set()
        text_box = ctk.CTkTextbox(popup, width=450, height=150)
        text_box.pack(padx=20, pady=10)
        text_box.insert("1.0", message)
        text_box.configure(state="disabled")
        ctk.CTkButton(popup, text="OK", command=popup.destroy).pack(pady=10)