import tkinter as tk
from tkinter import ttk

class OpenAccount(tk.Toplevel):
    """ A 'megawidget' for opening a new bank account """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.title("Open Account")

        # Make sure that the popup window is close to the button so that the user does not have to move much
        x = parent.winfo_x()
        y = parent.winfo_y()
        self.geometry(f"+{x + 50}+{y + 50}")

        # This variable will hold the account type chosen by the user
        self.account_type = None

        self.setup_widgets()
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def setup_widgets(self):
        """Setup labels, entries, and buttons."""
        self._account_type_label = ttk.Label(self, text="Account Type:")
        self._account_type_label.grid(row=0, column=0, padx=10, pady=10)

        self.account_type_var = tk.StringVar()
        self._account_type_dropdown = ttk.Combobox(
            self, textvariable=self.account_type_var, state='readonly')
        self._account_type_dropdown["values"] = ("checking", "savings")
        self._account_type_dropdown.grid(row=0, column=1, padx=10, pady=10)

        # Submit button
        self._submit_button = ttk.Button(self, text="Enter", command=self.enter)
        self._submit_button.grid(row=1, column=0, pady=10)

        # Cancel button
        self._cancel_button = ttk.Button(self, text="Cancel", command=self.cancel)
        self._cancel_button.grid(row=1, column=1, pady=10)

    def enter(self):
        """Handle enter actions."""
        account_type = self.account_type_var.get().lower()
        if account_type in ('checking', 'savings'):
            self.account_type = account_type
            self.destroy()  
        else:
         
            print("Please select a valid account type!")

    def cancel(self):
        """Handle cancel actions."""
        self.account_type = None 
        self.destroy()  

    def get_account_type(self):
        """After the window is destroyed, this method can be used to retrieve the selection."""
        return self.account_type


