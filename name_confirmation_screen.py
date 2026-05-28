# ui/name_confirmation_screen.py
"""
Name Confirmation Screen - Group similar names and confirm with user.
Redesigned to match the format of Review Extracted Account Names screen.
"""

import customtkinter as ctk
from typing import List, Dict, Tuple
import tkinter as tk
from tkinter import ttk


class NameConfirmationScreen(ctk.CTkFrame):
    """
    Stage 1: User confirms/rejects similar name groupings.
    Enhanced with better UI and individual name selection within groups.
    """
    
    def __init__(self, master, grouped_names: List[List[str]], on_complete):
        super().__init__(master)
        
        self.grouped_names = grouped_names
        self.on_complete = on_complete
        
        # Filter groups with more than 1 name (need confirmation)
        self.groups_to_confirm = [g for g in grouped_names if len(g) > 1]
        # Single names are auto-confirmed
        self.auto_confirmed = [g[0] for g in grouped_names if len(g) == 1]
        
        self.current_group_index = 0
        self.confirmed_mappings = {}  # Maps original name -> final name/primary
        self.name_aliases = {}  # Maps alias -> primary name
        
        # Initialize all auto-confirmed names
        for name in self.auto_confirmed:
            self.confirmed_mappings[name] = name
        
        # Track checkboxes for individual selections
        self.checkbox_vars = {}
        self.checkbox_widgets = {}
        
        self._create_ui()
        
        if self.groups_to_confirm:
            self._load_current_group()
        else:
            self._finish_confirmation()

    def _create_ui(self):
        """Create the main UI"""
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=15, padx=20, sticky="ew")
        
        ctk.CTkLabel(
            header_frame,
            text="Confirm Similar Account Names",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")
        
        # Stats
        total_groups = len(self.grouped_names)
        needs_review = len(self.groups_to_confirm)
        auto_confirmed = len(self.auto_confirmed)
        
        stats_text = f"{total_groups} groups | {needs_review} need review | {auto_confirmed} auto-confirmed"
        
        self.stats_label = ctk.CTkLabel(
            header_frame,
            text=stats_text,
            font=ctk.CTkFont(size=12),
            text_color="#FF9800" if needs_review > 0 else "#4CAF50"
        )
        self.stats_label.pack(side="right")
        
        # Info label
        ctk.CTkLabel(
            self,
            text="Review groups of similar names. Select which names refer to the same account.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")
        
        # Filter toolbar
        toolbar_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        toolbar_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(toolbar_frame, text="Filter:").pack(side="left", padx=10)
        
        self.filter_var = ctk.StringVar(value="All Groups")
        filter_dropdown = ctk.CTkComboBox(
            toolbar_frame,
            values=["All Groups", "Pending Review", "Completed"],
            variable=self.filter_var,
            width=150,
            command=self._apply_filter
        )
        filter_dropdown.pack(side="left", padx=5)
        
        ctk.CTkLabel(toolbar_frame, text="Search:").pack(side="left", padx=(20, 5))
        
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(toolbar_frame, textvariable=self.search_var, width=200)
        search_entry.pack(side="left", padx=5)
        search_entry.bind('<KeyRelease>', self._apply_filter)
        
        # Bulk actions
        ctk.CTkButton(
            toolbar_frame,
            text="Group All Remaining",
            fg_color="#4CAF50",
            width=150,
            command=self._group_all_remaining
        ).pack(side="right", padx=10)
        
        ctk.CTkButton(
            toolbar_frame,
            text="Separate All Remaining",
            fg_color="gray",
            width=150,
            command=self._separate_all_remaining
        ).pack(side="right", padx=5)
        
        # Main content - Treeview
        self._create_table()
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=20, pady=15, sticky="ew")
        
        ctk.CTkButton(
            btn_frame,
            text="← Back",
            fg_color="gray",
            command=self._go_back
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_frame,
            text="Confirm & Continue →",
            fg_color="green",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._continue
        ).pack(side="right")

    def _create_table(self):
        """Create treeview table for name groups"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        tree_container = tk.Frame(table_frame, bg='#2b2b2b')
        tree_container.grid(row=0, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        columns = (
            'select', 'group_id', 'name', 'similar_names', 'status', 'action'
        )
        
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show='headings',
            selectmode='browse'
        )
        
        col_config = [
            ('select', 'Select', 60, tk.CENTER),
            ('group_id', 'Group', 60, tk.CENTER),
            ('name', 'Account Name', 250, tk.W),
            ('similar_names', 'Similar Names Found', 350, tk.W),
            ('status', 'Status', 100, tk.CENTER),
            ('action', 'Action', 150, tk.CENTER)
        ]
        
        for col_id, heading, width, anchor in col_config:
            self.tree.heading(col_id, text=heading, anchor=anchor)
            self.tree.column(col_id, width=width, anchor=anchor, minwidth=50)
        
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Style
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        
        style.configure("Treeview",
                       background="#2d2d2d",
                       foreground="#e0e0e0",
                       fieldbackground="#2d2d2d",
                       font=('Segoe UI', 10),
                       rowheight=35)
        style.configure("Treeview.Heading",
                       background="#4a4a4a",
                       foreground="white",
                       font=('Segoe UI', 10, 'bold'))
        style.map('Treeview',
                 background=[('selected', '#1976D2')],
                 foreground=[('selected', 'white')])
        
        # Double click to view details
        self.tree.bind('<Double-1>', self._on_double_click)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            table_frame, 
            text="", 
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_label.grid(row=2, column=0, sticky="w", pady=5)

    def _load_current_group(self):
        """Load and display all groups in table"""
        self._populate_table()

    def _populate_table(self, filter_text=None, filter_type="All Groups"):
        """Populate table with name groups"""
        if self.tree is None:
            return
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        row_num = 0
        
        # First, add groups that need confirmation
        for group_idx, group in enumerate(self.groups_to_confirm):
            group_id = f"G{group_idx + 1}"
            
            # Check if this group is completed
            is_completed = any(name in self.confirmed_mappings for name in group)
            
            # Apply filters
            if filter_type == "Pending Review" and is_completed:
                continue
            elif filter_type == "Completed" and not is_completed:
                continue
            
            # Search filter
            if filter_text:
                search_lower = filter_text.lower()
                match_found = any(search_lower in str(name).lower() for name in group)
                if not match_found:
                    continue
            
            # Primary name (first in group)
            primary_name = group[0]
            
            # Similar names (rest of group)
            similar_names = ", ".join(group[1:]) if len(group) > 1 else "-"
            
            # Status
            if is_completed:
                status = "✓ Done"
                status_tag = 'completed'
            else:
                status = "⚠️ Review"
                status_tag = 'pending'
            
            # Action button text
            action = "Review" if not is_completed else "Change"
            
            values = (
                "☐" if not is_completed else "☑",
                group_id,
                primary_name,
                similar_names,
                status,
                action
            )
            
            tag = 'even' if row_num % 2 == 0 else 'odd'
            
            self.tree.insert('', tk.END, values=values, tags=(tag, status_tag))
            row_num += 1
        
        # Then add auto-confirmed single names
        for name in self.auto_confirmed:
            if filter_type == "Pending Review":
                continue
            
            if filter_text and filter_text.lower() not in str(name).lower():
                continue
            
            values = (
                "☑",
                "-",
                name,
                "(Unique name)",
                "✓ Auto",
                "-"
            )
            
            tag = 'even' if row_num % 2 == 0 else 'odd'
            
            self.tree.insert('', tk.END, values=values, tags=(tag, 'auto'))
            row_num += 1
        
        # Configure tags
        self.tree.tag_configure('even', background='#2d2d2d')
        self.tree.tag_configure('odd', background='#353535')
        self.tree.tag_configure('pending', foreground='#FF9800')
        self.tree.tag_configure('completed', foreground='#4CAF50')
        self.tree.tag_configure('auto', foreground='#2196F3')
        
        self._update_status()

    def _apply_filter(self, event=None):
        """Apply filter to table"""
        filter_type = self.filter_var.get()
        search_text = self.search_var.get()
        self._populate_table(search_text, filter_type)

    def _on_double_click(self, event):
        """Handle double click - open group detail view"""
        selected = self.tree.selection()
        if not selected:
            return
        
        item = selected[0]
        values = self.tree.item(item, 'values')
        
        if len(values) < 3:
            return
        
        group_id = values[1]
        
        if group_id == "-":
            return  # Auto-confirmed single name
        
        # Extract group number
        try:
            group_num = int(group_id.replace("G", "")) - 1
            if 0 <= group_num < len(self.groups_to_confirm):
                self._show_group_detail(group_num)
        except:
            pass

    def _show_group_detail(self, group_index):
        """Show detailed view for a group"""
        group = self.groups_to_confirm[group_index]
        group_id = f"G{group_index + 1}"
        
        popup = ctk.CTkToplevel(self)
        popup.title(f"Review Group {group_id}")
        popup.geometry("600x500")
        popup.grab_set()
        
        # Header
        header_frame = ctk.CTkFrame(popup, fg_color=("gray80", "gray20"))
        header_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header_frame,
            text=f"Group {group_id} - {len(group)} similar names",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FF9800"
        ).pack(pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="Select the primary name and mark which names refer to the same account:",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=(0, 10))
        
        # Scrollable frame for names
        scroll_frame = ctk.CTkScrollableFrame(popup)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Checkbox variables for this group
        group_check_vars = {}
        primary_var = ctk.StringVar(value=group[0])
        
        for i, name in enumerate(group):
            name_frame = ctk.CTkFrame(scroll_frame, fg_color=("gray75", "gray25"), corner_radius=8)
            name_frame.pack(fill="x", pady=5)
            
            # Checkbox for selection
            check_var = ctk.BooleanVar(value=True)
            group_check_vars[name] = check_var
            
            check = ctk.CTkCheckBox(
                name_frame,
                text="",
                variable=check_var,
                width=30
            )
            check.pack(side="left", padx=10)
            
            # Radio button for primary selection
            radio = ctk.CTkRadioButton(
                name_frame,
                text=name,
                variable=primary_var,
                value=name,
                font=ctk.CTkFont(size=12)
            )
            radio.pack(side="left", padx=10)
            
            # Show normalized version
            from engine.matcher import normalize_name
            normalized = normalize_name(name)
            if normalized != name.upper():
                ctk.CTkLabel(
                    name_frame,
                    text=f"({normalized})",
                    font=ctk.CTkFont(size=9),
                    text_color="gray"
                ).pack(side="right", padx=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save_group():
            primary = primary_var.get()
            
            # Save mappings
            for name in group:
                if group_check_vars[name].get():
                    # This name is part of the group
                    self.confirmed_mappings[name] = primary
                    if name != primary:
                        self.name_aliases[name] = primary
                else:
                    # This name is separate
                    self.confirmed_mappings[name] = name
            
            popup.destroy()
            self._populate_table(self.search_var.get(), self.filter_var.get())
        
        def separate_all():
            for name in group:
                self.confirmed_mappings[name] = name
            
            popup.destroy()
            self._populate_table(self.search_var.get(), self.filter_var.get())
        
        ctk.CTkButton(
            btn_frame,
            text="✓ Save Group",
            fg_color="green",
            width=120,
            command=save_group
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Separate All",
            fg_color="#FF9800",
            width=120,
            command=separate_all
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="gray",
            width=100,
            command=popup.destroy
        ).pack(side="left", padx=10)

    def _update_status(self):
        """Update status label"""
        total = len(self.tree.get_children())
        pending = len([g for g in self.groups_to_confirm if not any(name in self.confirmed_mappings for name in g)])
        completed = len(self.groups_to_confirm) - pending
        
        self.status_label.configure(
            text=f"Showing {total} | Pending: {pending} | Completed: {completed}"
        )

    def _group_all_remaining(self):
        """Group all remaining groups"""
        for group in self.groups_to_confirm:
            primary = group[0]
            for name in group:
                self.confirmed_mappings[name] = primary
                if name != primary:
                    self.name_aliases[name] = primary
        
        self._populate_table(self.search_var.get(), self.filter_var.get())
        self._show_success("Success", "All remaining groups have been merged!")

    def _separate_all_remaining(self):
        """Separate all remaining groups"""
        for group in self.groups_to_confirm:
            for name in group:
                self.confirmed_mappings[name] = name
        
        self._populate_table(self.search_var.get(), self.filter_var.get())
        self._show_success("Success", "All remaining groups have been separated!")

    def _go_back(self):
        """Go back"""
        if self.on_complete:
            self.on_complete(None, None)

    def _continue(self):
        """Continue to next screen"""
        # Check if all groups are completed
        pending = [g for g in self.groups_to_confirm if not any(name in self.confirmed_mappings for name in g)]
        
        if pending:
            self._show_warning(
                "Incomplete",
                f"{len(pending)} group(s) still need review.\n\n"
                "Please review all groups or use bulk actions."
            )
            return
        
        # Build final confirmed names list
        confirmed_names = []
        seen = set()
        
        # Add all unique primary names
        for name, final in self.confirmed_mappings.items():
            if final not in seen:
                confirmed_names.append(final)
                seen.add(final)
        
        # Add auto-confirmed names
        for name in self.auto_confirmed:
            if name not in seen:
                confirmed_names.append(name)
                seen.add(name)
        
        print(f"Final confirmed names: {confirmed_names}")
        print(f"Aliases: {self.name_aliases}")
        
        if self.on_complete:
            self.on_complete(confirmed_names, self.name_aliases)

    def _show_success(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("350x120")
        popup.grab_set()
        ctk.CTkLabel(popup, text=message, text_color="#4CAF50").pack(expand=True, pady=20)
        ctk.CTkButton(popup, text="OK", command=popup.destroy).pack(pady=10)

    def _show_warning(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("400x150")
        popup.grab_set()
        ctk.CTkLabel(popup, text=message, text_color="#FF9800").pack(expand=True, pady=20)
        ctk.CTkButton(popup, text="OK", command=popup.destroy).pack(pady=10)