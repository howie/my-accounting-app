import tkinter as tk
from tkinter import ttk

from myab.ui.account_management import AccountManagementFrame
from myab.ui.transaction_list import TransactionListFrame

class MainWindow(tk.Tk):
    def __init__(self, account_service, transaction_service, ledger_id):
        super().__init__()
        self.title("My Accounting Book")
        self.geometry("800x600")
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')
        
        # Accounts Tab
        self.accounts_frame = AccountManagementFrame(self.notebook, account_service, ledger_id)
        self.notebook.add(self.accounts_frame, text="Accounts")
        
        # Transactions Tab
        self.transactions_frame = TransactionListFrame(self.notebook, transaction_service, ledger_id)
        self.notebook.add(self.transactions_frame, text="Transactions")
