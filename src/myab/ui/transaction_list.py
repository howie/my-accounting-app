import tkinter as tk
from tkinter import ttk

class TransactionListFrame(ttk.Frame):
    def __init__(self, parent, transaction_service, ledger_id):
        super().__init__(parent)
        self.transaction_service = transaction_service
        self.ledger_id = ledger_id
        self.create_widgets()
        
    def create_widgets(self):
        ttk.Label(self, text="Transaction History").pack()
        # Search bar
        # Treeview
