from tkinter import ttk

class TransactionEntryFrame(ttk.Frame):
    def __init__(self, parent, transaction_service, account_service, ledger_id):
        super().__init__(parent)
        self.transaction_service = transaction_service
        self.account_service = account_service
        self.ledger_id = ledger_id
        self.create_widgets()
        
    def create_widgets(self):
        ttk.Label(self, text="New Transaction").pack()
        # Inputs for Date, Type, Accounts, Amount, Description
        # Submit Button
