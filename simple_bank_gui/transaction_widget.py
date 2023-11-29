import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry  
from decimal import Decimal, InvalidOperation

class AddTransaction(tk.Toplevel):
    """A 'megawidget' for adding a new transaction"""

    def __init__(self, parent, last_transaction_date, balance, **kwargs):
        super().__init__(parent, **kwargs)
        self.title("Add Transaction")

        # Position the window close to the parent
        x = parent.winfo_x()
        y = parent.winfo_y()
        self.geometry(f"+{x + 50}+{y + 50}")
        self._last_transaction_date = last_transaction_date
        self.setup_widgets()
        self._balance = balance
        self.protocol("WM_DELETE_WINDOW", self.on_close) 

        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def setup_widgets(self):
        """Setup labels, entries, and buttons."""

        self._amount_label = ttk.Label(self, text="Amount:")
        self._amount_label.grid(row=0, column=0, padx=10, pady=10)

        self._amount_entry = ttk.Entry(self)
        self._amount_entry.grid(row=0, column=1, padx=10, pady=10)

        self._date_label = ttk.Label(self, text="Date:")
        self._date_label.grid(row=1, column=0, padx=10, pady=10)

        self._date_entry = DateEntry(self)
        self._date_entry.grid(row=1, column=1, padx=10, pady=10)

        self._validation_message = ttk.Label(self, text="", foreground="red")
        self._validation_message.grid(row=2, column=0, columnspan=2)

        # Here we create a frame that will hold our buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky='ew')  # make sure it spans across both columns

        # Make Enter button disabled until the user selects an option. 
        self._enter_button = ttk.Button(button_frame, text="Enter", command=self.enter, state="disabled")
        self._enter_button.pack(side='left', padx=10, expand=True)  

        self._cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        self._cancel_button.pack(side='left', padx=10, expand=True)

        # Input validation
        self._amount_entry.bind("<KeyRelease>", self.validate_input)
        self._date_entry.bind("<<DateEntrySelected>>", self.validate_input)


    def validate_input(self, event):
        """Validate inputs and provide feedback."""
        amount = self._amount_entry.get()
        selected_date = self._date_entry.get_date()  

        current_balance = Decimal(self._balance)  

        try:
            # Validate amount
            try:
                amount_value = Decimal(amount)
            except InvalidOperation:
                raise ValueError("Please enter a valid number.")

            if amount_value + current_balance < 0:
                raise ValueError("You don't have enough funds.")

            if self._last_transaction_date is not None and selected_date < self._last_transaction_date:
                raise ValueError(f"Date must be on or after {self._last_transaction_date}")

            # Valid response 
            self._enter_button["state"] = "normal"
            self._validation_message["text"] = ""

        except ValueError as e:
            self._validation_message["text"] = str(e)
            self._enter_button["state"] = "disabled"



    def enter(self):
        """Handle enter actions."""
        try:
            self.transaction_amount = float(self._amount_entry.get())
            self.transaction_date = self._date_entry.get_date()  
        except ValueError:
            print("Invalid input. Amount should be a number.")
            return

        self.destroy()

    def cancel(self):
        """Handle cancel actions."""
        self.transaction_amount = None  
        self.transaction_date = None
        self.destroy()

    def get_transaction_details(self):
        return self.transaction_amount, self.transaction_date

    def on_close(self):
        self.transaction_amount = None
        self.transaction_date = None
        self.destroy()
