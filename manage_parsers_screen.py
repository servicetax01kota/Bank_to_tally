# ui/manage_parsers_screen.py
"""
Manage Parsers Screen - Add and manage bank parsers.
Allows users to add custom bank parsers without modifying core code.
"""

import customtkinter as ctk
from engine.parser_manager import get_parser_manager
import tkinter.filedialog as fd
import os


class ManageParsersScreen(ctk.CTkFrame):
    """
    Screen for users to add/manage bank parsers.
    """
    
    def __init__(self, master, on_back):
        super().__init__(master)
        
        self.on_back = on_back
        self.parser_manager = get_parser_manager()
        
        self._create_ui()
        self._load_parsers()
    
    def _create_ui(self):
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=15, padx=20, sticky="ew")
        
        ctk.CTkLabel(
            header_frame,
            text="Manage Bank Parsers",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            header_frame,
            text="← Back",
            fg_color="gray",
            width=80,
            command=self.on_back
        ).pack(side="right")
        
        # Info
        info_frame = ctk.CTkFrame(self, fg_color=("#e3f2fd", "#1a237e"))
        info_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(
            info_frame,
            text="💡 Add custom bank parsers to extract account names from different bank statement formats.\n"
                 "Parsers use Python regex patterns to identify party names from transaction narrations.",
            font=ctk.CTkFont(size=11),
            text_color=("#1565c0", "#90caf9"),
            justify="left"
        ).pack(pady=10, padx=20)
        
        # Toolbar
        toolbar_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        toolbar_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        ctk.CTkButton(
            toolbar_frame,
            text="➕ Add New Parser",
            fg_color="#4CAF50",
            command=self._show_add_parser
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(
            toolbar_frame,
            text="📂 Import Parser File",
            fg_color="#2196F3",
            command=self._import_parser_file
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(
            toolbar_frame,
            text="🔄 Reload All",
            fg_color="#FF9800",
            command=self._reload_parsers
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(
            toolbar_frame,
            text="📋 View Template",
            fg_color="#9C27B0",
            command=self._view_template
        ).pack(side="right", padx=10, pady=10)
        
        # Parsers list
        self.parsers_frame = ctk.CTkScrollableFrame(self)
        self.parsers_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.parsers_frame.grid_columnconfigure(0, weight=1)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=20, pady=15, sticky="ew")
        
        ctk.CTkButton(
            btn_frame,
            text="Close",
            fg_color="gray",
            command=self.on_back
        ).pack(side="right")
    
    def _load_parsers(self):
        """Load and display all parsers"""
        for widget in self.parsers_frame.winfo_children():
            widget.destroy()
        
        parsers = self.parser_manager.get_all_banks()
        
        if not parsers:
            ctk.CTkLabel(
                self.parsers_frame,
                text="No parsers found. Add a new parser to get started.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack(pady=50)
            return
        
        # Header
        header_row = ctk.CTkFrame(self.parsers_frame, fg_color=("gray70", "gray30"))
        header_row.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        header_row.grid_columnconfigure(0, weight=3)
        header_row.grid_columnconfigure(1, weight=1)
        header_row.grid_columnconfigure(2, weight=1)
        
        ctk.CTkLabel(header_row, text="Bank Name", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(header_row, text="Type", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=10, pady=5)
        ctk.CTkLabel(header_row, text="Actions", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=10, pady=5)
        
        for i, parser in enumerate(parsers):
            self._create_parser_card(parser, i + 1)
    
    def _create_parser_card(self, parser, index):
        """Create a card for each parser"""
        card = ctk.CTkFrame(
            self.parsers_frame,
            fg_color=("gray80", "gray20") if index % 2 == 0 else "transparent"
        )
        card.grid(row=index, column=0, padx=5, pady=5, sticky="ew")
        card.grid_columnconfigure(0, weight=3)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=1)
        
        # Parser name and ID
        name_frame = ctk.CTkFrame(card, fg_color="transparent")
        name_frame.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        name_color = "#4CAF50" if parser.get('built_in') else "#2196F3"
        
        ctk.CTkLabel(
            name_frame,
            text=parser['name'],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=name_color
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            name_frame,
            text=f"ID: {parser['id']}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(anchor="w")
        
        # Type
        type_text = "Built-in" if parser.get('built_in') else "User Created"
        type_color = "#4CAF50" if parser.get('built_in') else "#FF9800"
        
        ctk.CTkLabel(
            card,
            text=type_text,
            font=ctk.CTkFont(size=11),
            text_color=type_color
        ).grid(row=0, column=1, padx=10, pady=10)
        
        # Actions
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.grid(row=0, column=2, padx=10, pady=10)
        
        ctk.CTkButton(
            actions_frame,
            text="Test",
            width=60,
            fg_color="#2196F3",
            command=lambda p=parser: self._test_parser(p['id'])
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            actions_frame,
            text="View",
            width=60,
            fg_color="gray",
            command=lambda p=parser: self._view_parser(p['id'])
        ).pack(side="left", padx=2)
        
        if not parser.get('built_in'):
            ctk.CTkButton(
                actions_frame,
                text="Export",
                width=60,
                fg_color="#9C27B0",
                command=lambda p=parser: self._export_parser(p['id'])
            ).pack(side="left", padx=2)
    
    def _show_add_parser(self):
        """Show dialog to add new parser"""
        popup = ctk.CTkToplevel(self)
        popup.title("Add New Bank Parser")
        popup.geometry("700x600")
        popup.grab_set()
        
        # Bank name
        ctk.CTkLabel(popup, text="Bank Name:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        bank_name_var = ctk.StringVar()
        ctk.CTkEntry(popup, textvariable=bank_name_var, width=650).pack(padx=20)
        
        # Parser ID
        ctk.CTkLabel(popup, text="Parser ID (no spaces, lowercase, e.g., 'hdfc_bank'):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        parser_id_var = ctk.StringVar()
        ctk.CTkEntry(popup, textvariable=parser_id_var, width=650).pack(padx=20)
        
        # Code editor
        ctk.CTkLabel(popup, text="Parser Code:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        code_text = ctk.CTkTextbox(popup, width=650, height=300)
        code_text.pack(padx=20, pady=5)
        
        # Insert template
        template = self._get_parser_template()
        code_text.insert("1.0", template)
        
        # Buttons
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        def save_parser():
            bank_name = bank_name_var.get().strip()
            parser_id = parser_id_var.get().strip()
            code = code_text.get("1.0", "end")
            
            if not bank_name or not parser_id:
                self._show_error("Error", "Bank name and Parser ID are required")
                return
            
            if 'def extract(' not in code:
                self._show_error("Error", "Parser code must contain a 'def extract(narration)' function")
                return
            
            result = self.parser_manager.add_user_parser(parser_id, bank_name, code)
            
            if result['success']:
                test_info = ""
                if result.get('test_results'):
                    tr = result['test_results']
                    test_info = f"\n\nTest Results:\nPassed: {tr.get('passed', 0)}/{tr.get('total', 0)}"
                
                self._show_success("Success", f"Parser '{bank_name}' added successfully!{test_info}")
                popup.destroy()
                self._load_parsers()
            else:
                self._show_error("Error", result.get('error', 'Unknown error'))
        
        ctk.CTkButton(btn_frame, text="💾 Save Parser", fg_color="green", width=120, command=save_parser).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🧪 Test First", fg_color="#2196F3", width=120, command=lambda: self._test_code(code_text.get("1.0", "end"))).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="❌ Cancel", fg_color="gray", width=100, command=popup.destroy).pack(side="left", padx=10)
    
    def _get_parser_template(self):
        """Return parser code template"""
        return '''# Custom Bank Parser
# BANK_NAME: Display name for this bank

BANK_NAME = "Your Bank Name Here"

import re


def extract(narration):
    """
    Extract party name from bank narration.
    
    Args:
        narration: Bank statement narration text
        
    Returns:
        str: Extracted party name
        None: No identifiable party found
    """
    if not narration:
        return None
    
    narration = str(narration).strip()
    upper_n = narration.upper()
    
    # ============================================
    # CASH RELATED
    # ============================================
    if any(keyword in upper_n for keyword in ['CASH DEPOSIT', 'CASH CHEQUE', 'CASH WDL']):
        return 'Cash'
    
    # ============================================
    # BANK CHARGES / ATM
    # ============================================
    if any(keyword in upper_n for keyword in ['ATMCARD', 'ATM CARD', 'CHARGES', 'FEE']):
        return 'Bank Charges'
    
    # ============================================
    # UPI PATTERNS
    # Add your UPI patterns here
    # ============================================
    # if 'UPI/' in upper_n:
    #     upi_match = re.search(r'UPI/(?:CR|DR)/([^/]+)/([^/]+)/', narration)
    #     if upi_match:
    #         return upi_match.group(2).strip()
    
    # ============================================
    # NEFT PATTERNS
    # Add your NEFT patterns here
    # ============================================
    # if 'NEFT' in upper_n:
    #     neft_match = re.search(r'NEFT\\*.*?\\*.*?\\*([^*]+)--', narration)
    #     if neft_match:
    #         return neft_match.group(1).strip()
    
    # ============================================
    # RTGS PATTERNS
    # Add your RTGS patterns here
    # ============================================
    # if 'RTGS' in upper_n:
    #     rtgs_match = re.search(r'RTGS.*--([A-Z].+)', narration)
    #     if rtgs_match:
    #         return rtgs_match.group(1).strip()
    
    # ============================================
    # CHEQUE PATTERNS
    # Add your cheque patterns here
    # ============================================
    # if 'CHEQUE WDL' in upper_n:
    #     return None  # No identifiable party
    
    # ============================================
    # ADD YOUR CUSTOM PATTERNS BELOW
    # ============================================
    
    
    return None


def test_parser():
    """
    Test function to validate parser.
    Modify test cases with your bank's actual formats.
    """
    test_cases = [
        # (narration, expected_result)
        ("Sample narration 1", "Expected Name 1"),
        ("Sample narration 2", None),
        ("CASH DEPOSIT--12345", "Cash"),
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
            'narration': narration[:60],
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
'''
    
    def _test_code(self, code):
        """Test parser code without saving"""
        try:
            # Create temporary parser
            exec(code, {})
            
            if 'extract' not in dir():
                self._show_error("Error", "No 'extract' function found in code")
                return
            
            self._show_success("Code Valid", "Parser code is syntactically valid!")
            
        except SyntaxError as e:
            self._show_error("Syntax Error", f"Line {e.lineno}: {e.msg}")
        except Exception as e:
            self._show_error("Error", str(e))
    
    def _import_parser_file(self):
        """Import parser from Python file"""
        filepath = fd.askopenfilename(
            title="Import Parser File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            
            # Extract bank name from code
            bank_name = os.path.basename(filepath)[:-3]  # Remove .py
            parser_id = bank_name.lower().replace(' ', '_')
            
            # Try to get BANK_NAME from code
            name_match = __import__('re').search(r'BANK_NAME\s*=\s*["\']([^"\']+)["\']', code)
            if name_match:
                bank_name = name_match.group(1)
                parser_id = bank_name.lower().replace(' ', '_')
            
            # Show in add dialog
            self._show_add_parser_with_data(bank_name, parser_id, code)
            
        except Exception as e:
            self._show_error("Import Error", str(e))
    
    def _show_add_parser_with_data(self, bank_name, parser_id, code):
        """Show add parser dialog with pre-filled data"""
        popup = ctk.CTkToplevel(self)
        popup.title("Import Parser")
        popup.geometry("700x600")
        popup.grab_set()
        
        ctk.CTkLabel(popup, text="Bank Name:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        bank_name_var = ctk.StringVar(value=bank_name)
        ctk.CTkEntry(popup, textvariable=bank_name_var, width=650).pack(padx=20)
        
        ctk.CTkLabel(popup, text="Parser ID:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        parser_id_var = ctk.StringVar(value=parser_id)
        ctk.CTkEntry(popup, textvariable=parser_id_var, width=650).pack(padx=20)
        
        ctk.CTkLabel(popup, text="Parser Code:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        code_text = ctk.CTkTextbox(popup, width=650, height=300)
        code_text.pack(padx=20, pady=5)
        code_text.insert("1.0", code)
        
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        def save_parser():
            result = self.parser_manager.add_user_parser(
                parser_id_var.get().strip(),
                bank_name_var.get().strip(),
                code_text.get("1.0", "end")
            )
            
            if result['success']:
                self._show_success("Success", f"Parser imported successfully!")
                popup.destroy()
                self._load_parsers()
            else:
                self._show_error("Error", result.get('error', 'Unknown error'))
        
        ctk.CTkButton(btn_frame, text="💾 Save", fg_color="green", command=save_parser).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="❌ Cancel", fg_color="gray", command=popup.destroy).pack(side="left", padx=10)
    
    def _test_parser(self, parser_id):
        """Test a specific parser"""
        result = self.parser_manager.test_parser(parser_id)
        
        if not result['success']:
            self._show_error("Test Error", result.get('error', 'Unknown error'))
            return
        
        test_results = result['results']
        
        popup = ctk.CTkToplevel(self)
        popup.title(f"Test Results - {parser_id}")
        popup.geometry("600x400")
        popup.grab_set()
        
        # Summary
        summary_frame = ctk.CTkFrame(popup, fg_color=("gray80", "gray20"))
        summary_frame.pack(fill="x", padx=20, pady=20)
        
        passed = test_results['passed']
        total = test_results['total']
        failed = test_results['failed']
        
        color = "#4CAF50" if failed == 0 else "#FF9800" if passed > 0 else "#F44336"
        
        ctk.CTkLabel(
            summary_frame,
            text=f"Passed: {passed}/{total}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=color
        ).pack(pady=10)
        
        # Results
        results_frame = ctk.CTkScrollableFrame(popup)
        results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        for r in test_results['results']:
            row = ctk.CTkFrame(results_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            status_color = "#4CAF50" if r['status'] == "PASS" else "#F44336"
            status_symbol = "✓" if r['status'] == "PASS" else "✗"
            
            ctk.CTkLabel(row, text=f"{status_symbol} {r['narration'][:40]}", text_color=status_color).pack(side="left")
            ctk.CTkLabel(row, text=f"Expected: {r['expected']}").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"Got: {r['got']}", text_color="gray").pack(side="right")
        
        ctk.CTkButton(popup, text="Close", command=popup.destroy).pack(pady=10)
    
    def _view_parser(self, parser_id):
        """View parser code"""
        parser = self.parser_manager.parsers.get(parser_id)
        if not parser:
            return
        
        try:
            module = __import__(parser['module_path'], fromlist=[''])
            import inspect
            code = inspect.getsource(module)
        except:
            code = "# Could not load source code"
        
        popup = ctk.CTkToplevel(self)
        popup.title(f"Parser Code - {parser['name']}")
        popup.geometry("700x500")
        popup.grab_set()
        
        text_box = ctk.CTkTextbox(popup, width=650, height=400)
        text_box.pack(padx=20, pady=20)
        text_box.insert("1.0", code)
        text_box.configure(state="disabled")
        
        ctk.CTkButton(popup, text="Close", command=popup.destroy).pack(pady=10)
    
    def _export_parser(self, parser_id):
        """Export parser to file"""
        parser = self.parser_manager.parsers.get(parser_id)
        if not parser:
            return
        
        filepath = fd.asksaveasfilename(
            title="Export Parser",
            defaultextension=".py",
            initialfile=f"{parser_id}.py"
        )
        
        if not filepath:
            return
        
        try:
            module = __import__(parser['module_path'], fromlist=[''])
            import inspect
            code = inspect.getsource(module)
            
            with open(filepath, 'w') as f:
                f.write(code)
            
            self._show_success("Success", f"Parser exported to:\n{filepath}")
            
        except Exception as e:
            self._show_error("Export Error", str(e))
    
    def _reload_parsers(self):
        """Reload all parsers"""
        self.parser_manager.reload_parsers()
        self._load_parsers()
        self._show_success("Success", "All parsers reloaded successfully!")
    
    def _view_template(self):
        """View parser template"""
        popup = ctk.CTkToplevel(self)
        popup.title("Parser Template")
        popup.geometry("700x500")
        popup.grab_set()
        
        text_box = ctk.CTkTextbox(popup, width=650, height=400)
        text_box.pack(padx=20, pady=20)
        text_box.insert("1.0", self._get_parser_template())
        text_box.configure(state="disabled")
        
        ctk.CTkButton(popup, text="Close", command=popup.destroy).pack(pady=10)
    
    def _show_error(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("400x150")
        popup.grab_set()
        ctk.CTkLabel(popup, text=message, wraplength=350).pack(expand=True, pady=20)
        ctk.CTkButton(popup, text="OK", command=popup.destroy).pack(pady=10)
    
    def _show_success(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("400x150")
        popup.grab_set()
        ctk.CTkLabel(popup, text=message, wraplength=350, text_color="#4CAF50").pack(expand=True, pady=20)
        ctk.CTkButton(popup, text="OK", command=popup.destroy).pack(pady=10)