import tkinter as tk
from tkinter import messagebox
from src.myab.persistence.database import initialize_database, get_db_connection
from src.myab.persistence.repositories.user_account_repository import UserAccountRepository
from src.myab.persistence.repositories.ledger_repository import LedgerRepository
from src.myab.persistence.repositories.account_repository import AccountRepository
from src.myab.persistence.repositories.transaction_repository import TransactionRepository
from src.myab.services.user_account_service import UserAccountService
from src.myab.services.ledger_service import LedgerService
from src.myab.services.account_service import AccountService
from src.myab.services.transaction_service import TransactionService
from src.myab.validation.validators import TransactionValidator
import os

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MyAB - My Accounting App")
        self.geometry("800x600")

        self.db_file = os.path.join(os.getcwd(), "myab.db")
        initialize_database(self.db_file)

        # Initialize Repositories
        self.user_account_repo = UserAccountRepository(self.db_file)
        self.ledger_repo = LedgerRepository(self.db_file)
        self.account_repo = AccountRepository(self.db_file)
        self.transaction_repo = TransactionRepository(self.db_file)

        # Initialize Services
        self.user_account_service = UserAccountService(self.user_account_repo)
        self.account_service = AccountService(self.account_repo)
        self.transaction_validator = TransactionValidator(self.account_repo)
        self.transaction_service = TransactionService(self.transaction_repo, self.account_repo, self.transaction_validator)
        self.ledger_service = LedgerService(self.ledger_repo, self.account_service, self.transaction_service)

        self._create_widgets()

    def _create_widgets(self):
        # Frame for user creation/login
        user_frame = tk.LabelFrame(self, text="User Management", padx=10, pady=10)
        user_frame.pack(pady=10)

        tk.Label(user_frame, text="Username:").grid(row=0, column=0, sticky="w")
        self.username_entry = tk.Entry(user_frame)
        self.username_entry.grid(row=0, column=1)

        tk.Label(user_frame, text="Password:").grid(row=1, column=0, sticky="w")
        self.password_entry = tk.Entry(user_frame, show="*")
        self.password_entry.grid(row=1, column=1)

        create_user_btn = tk.Button(user_frame, text="Create User", command=self._create_user)
        create_user_btn.grid(row=2, column=0, pady=5)

        login_btn = tk.Button(user_frame, text="Login", command=self._login_user)
        login_btn.grid(row=2, column=1, pady=5)

        self.current_user_label = tk.Label(self, text="Not logged in.")
        self.current_user_label.pack()

        # Frame for Ledger creation (visible after login)
        self.ledger_frame = tk.LabelFrame(self, text="Ledger Management", padx=10, pady=10)
        
        tk.Label(self.ledger_frame, text="Ledger Name:").grid(row=0, column=0, sticky="w")
        self.ledger_name_entry = tk.Entry(self.ledger_frame)
        self.ledger_name_entry.grid(row=0, column=1)

        tk.Label(self.ledger_frame, text="Initial Cash:").grid(row=1, column=0, sticky="w")
        self.initial_cash_entry = tk.Entry(self.ledger_frame)
        self.initial_cash_entry.grid(row=1, column=1)

        create_ledger_btn = tk.Button(self.ledger_frame, text="Create Ledger", command=self._create_ledger)
        create_ledger_btn.grid(row=2, column=0, columnspan=2, pady=5)


    def _create_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user, msg = self.user_account_service.create_user_account(username, password)
        if user:
            messagebox.showinfo("Success", f"User '{username}' created.")
            self.current_user = user
            self._update_user_status()
            self.ledger_frame.pack(pady=10)
        else:
            messagebox.showerror("Error", msg)

    def _login_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user = self.user_account_service.authenticate_user(username, password)
        if user:
            messagebox.showinfo("Success", f"Logged in as '{username}'.")
            self.current_user = user
            self._update_user_status()
            self.ledger_frame.pack(pady=10)
        else:
            messagebox.showerror("Error", "Invalid username or password.")
            self.current_user = None
            self._update_user_status()
            self.ledger_frame.pack_forget()


    def _update_user_status(self):
        if hasattr(self, 'current_user') and self.current_user:
            self.current_user_label.config(text=f"Logged in as: {self.current_user.username}")
        else:
            self.current_user_label.config(text="Not logged in.")

    def _create_ledger(self):
        if not hasattr(self, 'current_user') or not self.current_user:
            messagebox.showerror("Error", "Please login first to create a ledger.")
            return

        ledger_name = self.ledger_name_entry.get()
        initial_cash_str = self.initial_cash_entry.get()
        try:
            initial_cash = int(float(initial_cash_str) * 100) # Convert to cents
        except ValueError:
            messagebox.showerror("Error", "Initial cash must be a number.")
            return
        
        try:
            ledger = self.ledger_service.create_ledger(self.current_user.id, ledger_name, initial_cash)
            if ledger:
                messagebox.showinfo("Success", f"Ledger '{ledger_name}' created successfully!")
            else:
                messagebox.showerror("Error", "Failed to create ledger.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()