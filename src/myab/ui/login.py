from tkinter import ttk

class LoginFrame(ttk.Frame):
    def __init__(self, parent, user_service, on_login_success):
        super().__init__(parent)
        self.user_service = user_service
        self.on_login_success = on_login_success
        self.create_widgets()
        
    def create_widgets(self):
        ttk.Label(self, text="Login").pack()
        # Username, Password, Login Button
