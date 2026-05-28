# ui/tally_mapping_screen.py
"""
Tally Mapping Screen - Shows extracted names alongside Tally masters.
Similar to Name Confirmation Screen format.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Tuple
from engine.matcher import suggest_tally_master


LEDGER_GROUPS = [
    "Sundry Debtors",
    "Sundry Creditors",
    "Bank Accounts",
    "Cash-in-Hand",
    "Direct Expenses",
    "Indirect Expenses",
    "Direct Incomes",
    "Indirect Incomes",
    "Loans & Advances",
    "Capital Account",
    "Current Assets",
    "Current Liabilities",
    "Fixed Assets",
    "Investments",
    "Branch/Divisions",
    "Sales Accounts",
    "Purchase Accounts",
    "Duties & Taxes",
    "Provisions",
    "Suspense A/c"
]


class TallyMappingScreen(ctk.CTkFrame):
    """Map extracted account names to existing Tally Masters."""
    
    def __init__(self, master, extracted_names: List[str], tally_names: List[str], on_complete):
        super().__init__(master)
        
        self.extracted_names = list(extracted_names) if extracted_names else []
        self.tally_names = list(tally_names) if tally_names else []
        self.on_complete = on_complete
        
        self.mappings = {}
        self.new_ledgers = set()
        self.ledger_groups = {}
        self.suggestions = {}
        
        self._generate_suggestions()
        self._create_ui()
        self._populate_table()
    
    def _generate_suggestions(self):
        """Generate suggestions for each extracted name"""
        try:
            from thefuzz import fuzz
            
            for extracted_name in self.extracted_names:
                best_match, best_score = suggest_tally_master(extracted_name, self.tally_names)
                
                self.suggestions[extracted_name] = {
                    'best_match': best_match,
                    'best_score': best_score,
                    'is_new': best_score < 75
                }
                
                if best_score >= 75:
                    self.mappings[extracted_name] = best_match
                else:
                    self.mappings[extracted_name] = extracted_name
                    self.new_ledgers.add(extracted_name)
                    self.ledger_groups[extracted_name] = self._suggest_group(extracted_name)
        except Exception as e:
            print(f"Error generating suggestions: {e}")
    
    def _create_ui(self):
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        ctk.CTkLabel(
            self,
            text="Map to Tally Masters",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, pady=20, padx=20, sticky="w")
        
        ctk.CTkLabel(
            self,
            text=f"Showing {len(self.extracted_names)} extracted accounts with Tally Master suggestions.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")
        
        # Toolbar
        toolbar_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        toolbar_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(toolbar_frame, text="Filter:").pack(side="left", padx=10)
        
        self.filter_var = tk.StringVar(value="All")
        filter_dropdown = ctk.CTkComboBox(
            toolbar_frame,
            values=["All", "Has Match", "No Match (New)"],
            variable=self.filter_var,
            width=150,
            command=self._apply_filter
        )
        filter_dropdown.pack(side="left", padx=5)
        
        ctk.CTkButton(
            toolbar_frame,
            text="Accept All Matches",
            fg_color="#4CAF50",
            width=140,
            command=self._accept_all_matches
        ).pack(side="right", padx=10)
        
        ctk.CTkButton(
            toolbar_frame,
            text="New -> Debtors",
            fg_color="#FF9800",
            width=120,
            command=lambda: self._bulk_set_group("Sundry Debtors")
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            toolbar_frame,
            text="New -> Creditors",
            fg_color="#2196F3",
            width=120,
            command=lambda: self._bulk_set_group("Sundry Creditors")
        ).pack(side="right", padx=5)
        
        # Table
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
        
        self.stats_label = ctk.CTkLabel(btn_frame, text="", text_color="gray")
        self.stats_label.pack(side="left", padx=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Confirm ->",
            fg_color="green",
            font=ctk.CTkFont(weight="bold"),
            command=self._continue
        ).pack(side="right")
    
    def _create_table(self):
        """Create treeview table"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        tree_container = tk.Frame(table_frame, bg='#2b2b2b')
        tree_container.grid(row=0, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        columns = ('extracted', 'tally_match', 'confidence', 'final', 'status')
        
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', selectmode='extended')
        
        self.tree.heading('extracted', text='Extracted Name')
        self.tree.heading('tally_match', text='Tally Master Match')
        self.tree.heading('confidence', text='Match %')
        self.tree.heading('final', text='Final Mapping')
        self.tree.heading('status', text='Status')
        
        self.tree.column('extracted', width=200, anchor='w')
        self.tree.column('tally_match', width=200, anchor='w')
        self.tree.column('confidence', width=80, anchor='center')
        self.tree.column('final', width=200, anchor='w')
        self.tree.column('status', width=100, anchor='center')
        
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        style.configure("Treeview", background="#2d2d2d", foreground="#e0e0e0", fieldbackground="#2d2d2d", font=('Segoe UI', 10), rowheight=25)
        style.configure("Treeview.Heading", background="#4a4a4a", foreground="white", font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1976D2')], foreground=[('selected', 'white')])
        
        self.tree.tag_configure('matched', foreground='#4CAF50')
        self.tree.tag_configure('partial', foreground='#FF9800')
        self.tree.tag_configure('new', foreground='#F44336')
        self.tree.tag_configure('even', background='#2d2d2d')
        self.tree.tag_configure('odd', background='#353535')
    
    def _populate_table(self, filter_type="All"):
        """Populate table"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        row_num = 0
        
        for extracted_name in self.extracted_names:
            suggestion = self.suggestions.get(extracted_name, {})
            best_match = suggestion.get('best_match', None)
            best_score = suggestion.get('best_score', 0)
            is_new = suggestion.get('is_new', True)
            
            if filter_type == "Has Match" and is_new:
                continue
            elif filter_type == "No Match (New)" and not is_new:
                continue
            
            if best_match and best_score >= 75:
                tally_display = best_match
                conf_display = f"{best_score}%"
                status = "Match"
                final_display = best_match
                tag = 'matched'
            elif best_match:
                tally_display = best_match
                conf_display = f"{best_score}%"
                status = "Partial"
                final_display = extracted_name
                tag = 'partial'
            else:
                tally_display = "No match"
                conf_display = "0%"
                status = "New"
                final_display = f"{extracted_name} (New)"
                tag = 'new'
            
            row_tag = 'even' if row_num % 2 == 0 else 'odd'
            
            self.tree.insert('', 'end', values=(
                extracted_name,
                tally_display,
                conf_display,
                final_display,
                status
            ), tags=(tag, row_tag))
            
            row_num += 1
        
        self._update_stats()
    
    def _apply_filter(self, event=None):
        self._populate_table(self.filter_var.get())
    
    def _accept_all_matches(self):
        for extracted_name in self.extracted_names:
            suggestion = self.suggestions.get(extracted_name, {})
            best_match = suggestion.get('best_match', None)
            best_score = suggestion.get('best_score', 0)
            
            if best_match and best_score >= 60:
                self.mappings[extracted_name] = best_match
                self.new_ledgers.discard(extracted_name)
                if extracted_name in self.ledger_groups:
                    del self.ledger_groups[extracted_name]
        
        self._populate_table()
    
    def _bulk_set_group(self, group):
        for name in self.new_ledgers:
            self.ledger_groups[name] = group
        self._populate_table()
    
    def _suggest_group(self, name):
        n = name.upper()
        if 'CASH' in n: return "Cash-in-Hand"
        if any(w in n for w in ['CHARGE', 'FEE']): return "Indirect Expenses"
        if any(w in n for w in ['BANK', 'HDFC', 'SBI']): return "Bank Accounts"
        if any(w in n for w in ['LOAN', 'FINANCE']): return "Loans & Advances"
        return "Sundry Debtors"
    
    def _update_stats(self):
        mapped = len(self.mappings) - len(self.new_ledgers)
        new = len(self.new_ledgers)
        self.stats_label.configure(text=f"Mapped: {mapped} | New: {new}")
    
    def _go_back(self):
        if self.on_complete:
            self.on_complete(None, None, None, True)
    
    def _continue(self):
        if self.on_complete:
            self.on_complete(self.mappings, list(self.new_ledgers), self.ledger_groups, False)