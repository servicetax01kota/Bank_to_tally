# ui/duplicate_check_screen.py
"""
Duplicate Check Screen - Check for duplicate entries against Tally Day Book.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from typing import List, Dict
from engine.tally_parser import TallyVoucher, check_duplicate_in_daybook


class DuplicateCheckScreen(ctk.CTkFrame):
    """
    Check for duplicate entries against Tally Day Book.
    """
    
    def __init__(self, master, transactions: List[Dict], 
                 daybook_vouchers: List[TallyVoucher], on_complete):
        super().__init__(master)
        
        self.transactions = transactions if transactions else []
        self.daybook_vouchers = daybook_vouchers if daybook_vouchers else []
        self.on_complete_callback = on_complete
        
        # Results
        self.duplicates = []
        self.non_duplicates = []
        self.user_decisions = {}  # Index -> 'skip' or 'include'
        
        self._create_ui()
        self._check_duplicates()
        self._show_results()
    
    def _create_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        ctk.CTkLabel(
            self,
            text="Duplicate Check - Day Book",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, pady=15, padx=20, sticky="w")
        
        # Summary frame
        self.summary_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        self.summary_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.total_label = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(weight="bold"))
        self.total_label.pack(side="left", padx=20, pady=10)
        
        self.duplicate_label = ctk.CTkLabel(self.summary_frame, text="", text_color="#FF9800")
        self.duplicate_label.pack(side="left", padx=20, pady=10)
        
        self.unique_label = ctk.CTkLabel(self.summary_frame, text="", text_color="#4CAF50")
        self.unique_label.pack(side="left", padx=20, pady=10)
        
        # Filter toolbar
        toolbar_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        toolbar_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(toolbar_frame, text="Filter:").pack(side="left", padx=10)
        
        self.filter_var = tk.StringVar(value="All")
        filter_dropdown = ctk.CTkComboBox(
            toolbar_frame,
            values=["All", "Duplicates Only", "Unique Only"],
            variable=self.filter_var,
            width=150,
            command=self._apply_filter
        )
        filter_dropdown.pack(side="left", padx=5)
        
        # Bulk actions
        ctk.CTkButton(
            toolbar_frame,
            text="Skip All Duplicates",
            fg_color="#F44336",
            command=self._skip_all_duplicates
        ).pack(side="right", padx=10)
        
        ctk.CTkButton(
            toolbar_frame,
            text="Include All",
            fg_color="#4CAF50",
            command=self._include_all
        ).pack(side="right", padx=5)
        
        # Results table
        self._create_table()
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=20, pady=15, sticky="ew")
        
        ctk.CTkButton(
            btn_frame,
            text="<- Back",
            fg_color="gray",
            command=self._go_back
        ).pack(side="left")
        
        self.remaining_label = ctk.CTkLabel(btn_frame, text="", text_color="gray")
        self.remaining_label.pack(side="left", padx=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Continue ->",
            fg_color="green",
            font=ctk.CTkFont(weight="bold"),
            command=self._continue
        ).pack(side="right")
    
    def _create_table(self):
        """Create results table"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        tree_container = tk.Frame(table_frame, bg='#2b2b2b')
        tree_container.grid(row=0, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        columns = ('date', 'party', 'amount', 'type', 'status', 'action')
        
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', selectmode='extended')
        
        self.tree.heading('date', text='Date')
        self.tree.heading('party', text='Party Name')
        self.tree.heading('amount', text='Amount')
        self.tree.heading('type', text='Type')
        self.tree.heading('status', text='Status')
        self.tree.heading('action', text='Action')
        
        self.tree.column('date', width=90, anchor='center')
        self.tree.column('party', width=200, anchor='w')
        self.tree.column('amount', width=100, anchor='e')
        self.tree.column('type', width=70, anchor='center')
        self.tree.column('status', width=100, anchor='center')
        self.tree.column('action', width=100, anchor='center')
        
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        style.configure("Treeview", background="#2d2d2d", foreground="#e0e0e0", fieldbackground="#2d2d2d", font=('Segoe UI', 9), rowheight=25)
        style.configure("Treeview.Heading", background="#4a4a4a", foreground="white", font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', '#1976D2')], foreground=[('selected', 'white')])
        
        self.tree.tag_configure('duplicate', foreground='#FF9800')
        self.tree.tag_configure('unique', foreground='#4CAF50')
        self.tree.tag_configure('even', background='#2d2d2d')
        self.tree.tag_configure('odd', background='#353535')
    
    def _check_duplicates(self):
        """Check each transaction against daybook"""
        self.duplicates = []
        self.non_duplicates = []
        self.user_decisions = {}
        
        print(f"\n=== Checking {len(self.transactions)} transactions against {len(self.daybook_vouchers)} daybook entries ===")
        
        for idx, trans in enumerate(self.transactions):
            trans_date = trans.get('date', '')
            amount = trans.get('amount', 0)
            party = trans.get('mapped_ledger', trans.get('extracted_name', ''))
            
            matches = check_duplicate_in_daybook(
                trans_date, amount, party, self.daybook_vouchers
            )
            
            if matches:
                self.duplicates.append({
                    'index': idx,
                    'transaction': trans,
                    'matches': matches
                })
                self.user_decisions[idx] = 'skip'  # Default to skip
            else:
                self.non_duplicates.append(trans)
        
        print(f"\nResults: {len(self.duplicates)} duplicates, {len(self.non_duplicates)} unique")
    
    def _show_results(self, filter_type="All"):
        """Display results"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        total = len(self.transactions)
        dup_count = len(self.duplicates)
        unique_count = len(self.non_duplicates)
        
        self.total_label.configure(text=f"Total: {total}")
        self.duplicate_label.configure(text=f"Duplicates: {dup_count}")
        self.unique_label.configure(text=f"Unique: {unique_count}")
        
        row_num = 0
        
        # Show duplicates first
        for dup in self.duplicates:
            if filter_type == "Unique Only":
                continue
                
            trans = dup['transaction']
            idx = dup['index']
            
            date_str = str(trans.get('date', ''))[:10] if trans.get('date') else '-'
            party = trans.get('mapped_ledger', trans.get('extracted_name', ''))[:25]
            amount = f"Rs.{trans.get('amount', 0):,.2f}"
            trans_type = trans.get('type', '-')
            status = "Duplicate"
            action = self.user_decisions.get(idx, 'skip')
            
            tag = 'duplicate' if action == 'skip' else 'unique'
            row_tag = 'even' if row_num % 2 == 0 else 'odd'
            
            self.tree.insert('', 'end', values=(date_str, party, amount, trans_type, status, action),
                           tags=(tag, row_tag))
            row_num += 1
        
        # Show unique transactions
        for trans in self.non_duplicates:
            if filter_type == "Duplicates Only":
                continue
            
            date_str = str(trans.get('date', ''))[:10] if trans.get('date') else '-'
            party = trans.get('mapped_ledger', trans.get('extracted_name', ''))[:25]
            amount = f"Rs.{trans.get('amount', 0):,.2f}"
            trans_type = trans.get('type', '-')
            status = "Unique"
            action = "include"
            
            tag = 'unique'
            row_tag = 'even' if row_num % 2 == 0 else 'odd'
            
            self.tree.insert('', 'end', values=(date_str, party, amount, trans_type, status, action),
                           tags=(tag, row_tag))
            row_num += 1
    
    def _apply_filter(self, event=None):
        self._show_results(self.filter_var.get())
    
    def _skip_all_duplicates(self):
        for dup in self.duplicates:
            self.user_decisions[dup['index']] = 'skip'
        self._show_results()
    
    def _include_all(self):
        for dup in self.duplicates:
            self.user_decisions[dup['index']] = 'include'
        self._show_results()
    
    def _go_back(self):
        if self.on_complete_callback:
            self.on_complete_callback(None)
    
    def _continue(self):
        """Continue with filtered transactions"""
        filtered = list(self.non_duplicates)
        
        for dup in self.duplicates:
            if self.user_decisions.get(dup['index']) == 'include':
                filtered.append(dup['transaction'])
        
        print(f"\nFinal: {len(filtered)} transactions to import ({len(self.duplicates) - sum(1 for d in self.duplicates if self.user_decisions.get(d['index']) == 'include')} duplicates skipped)")
        
        if self.on_complete_callback:
            self.on_complete_callback(filtered)