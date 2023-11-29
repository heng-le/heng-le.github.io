import tkinter as tk
from tkinter import messagebox
from bank import Bank 
import sqlalchemy
from sqlalchemy.orm.session import sessionmaker
from base import Base
import logging 
from accounts import Account
from tkinter import ttk
from account_widget import OpenAccount
from transaction_widget import AddTransaction
from exceptions import OverdrawError, TransactionLimitError, TransactionSequenceError
import sys
import customtkinter as ctk
from button import CustomButton

logging.basicConfig(filename='bank.log', level=logging.DEBUG,
                    format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class BankAppGUI(ctk.CTk):
    """Bank Application with GUI."""

    def __init__(self):

        # Setting up session 
        self._session = Session()
        self._bank = Bank()

        self._bank = self._session.query(Bank).first()
        if self._bank:
            # If a bank instance is retrieved from the database, log the event.
            logging.debug("Loaded from bank.db")

        if not self._bank:
            # If no bank instance exists, create a new one and add it to the session
            self._bank = Bank()
            self._session.add(self._bank)
            self._session.commit()
            logging.debug("Saved to bank.db")

        # Main window setup
        self._window = tk.Tk()
        self._window.title("My Bank")
        self._window.minsize(300, 200)


        # Putting some text for clarity
        self._text_frame = tk.Frame(self._window)
        self._text_frame.grid(row=0, column=0, pady=10, padx=10)  
        self._info_label = tk.Label(self._text_frame, text="Bank HL's GUI", font=("Helvetica", 16, "bold"))
        self._info_label.pack() 

        # Frame for buttons
        self._button_frame = tk.Frame(self._window)
        self._button_frame.grid(row=1, column=0, pady=10)
        
        # Adding the different buttons
        CustomButton(self._button_frame, text="Add Account", command=lambda: self._add_account(self._session)).pack(side=tk.LEFT, padx=10)
        CustomButton(self._button_frame, text="Add Transaction", command=self._add_transaction).pack(side=tk.LEFT, padx=10)
        CustomButton(self._button_frame, text="Add Interest/Fees", command=self._add_interest).pack(side=tk.LEFT, padx=10)

        # Add Help button 
        self._help_button_frame = tk.Frame(self._window)
        self._help_button_frame.grid(row=3, column=0, sticky='se')  

        # Creating the help button and placing it within the new frame.
        self._help_button = tk.Button(self._help_button_frame, text="Help", command=self.display_help)
        self._help_button.pack(side=tk.RIGHT, padx=10, pady=10)  

        # Treeview to display accounts and balances
        self._account_treeview = ttk.Treeview(self._window, columns=('Account', 'Transactions'), height=10)

        # Adjust column headings
        self._account_treeview.heading('#0', text='')  
        self._account_treeview.heading('Account', text='Account Details')  
        self._account_treeview.heading('Transactions', text='Transactions')

        # Adjust column widths
        self._account_treeview.column('#0', stretch=tk.NO, width=40)  
        self._account_treeview.column('Account', stretch=tk.YES, minwidth=250)
        self._account_treeview.column('Transactions', stretch=tk.YES)

        self._account_treeview.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

        # Creating a scrollbar
        self._scrollbar = tk.Scrollbar(self._window, orient="vertical")
        self._scrollbar.grid(row=2, column=1, sticky='ns') 
        self._account_treeview.config(yscrollcommand=self._scrollbar.set)
        self._scrollbar.config(command=self._account_treeview.yview)

        self._account_treeview.bind('<ButtonRelease-1>', self._on_account_selected)

        # Resizing functionality
        self._window.grid_rowconfigure(2, weight=1)
        self._window.grid_columnconfigure(0, weight=1)

        self.populate_treeview(self._session) 

        self._window.mainloop()


    def create_custom_button(self, parent, text, command, side, padx, pady):
        """Creates a custom-styled button."""
        return tk.Button(parent, text=text, command=command,
                         bg="#009688",  
                         fg="white",  
                         padx=5,  
                         pady=5, 
                         font=("Helvetica", 12, "bold"),  
                         relief="flat",  
                         ).pack(side=side, padx=padx, pady=pady)


    def populate_treeview(self, session):
        """Method to be called when the Treeview widget needs to be updated with information from the SQL database."""
        accounts = session.query(Account).all()

        for row in self._account_treeview.get_children():
            self._account_treeview.delete(row)

        for account in accounts:
            entry = str(account)
            self._account_treeview.insert('', 'end', values=(entry, ""))


    def display_help(self):
        """Method to be called when the help button is pressed. This can be modified to do whatever you need."""
        messagebox.showinfo("Help", "Click on an account to select it. \nDouble click or press the '+' to show its transactions.")

    def _on_account_selected(self, event):
        selected_item = self._account_treeview.focus()
        account = self.get_account(selected_item)
        transactions = account.get_transactions()

        # Clear the previous transactions for the selected account
        for child in self._account_treeview.get_children(selected_item):
            self._account_treeview.delete(child)

        self._account_treeview.tag_configure("deposit", foreground="green")
        self._account_treeview.tag_configure("withdrawal", foreground="red")

        for transaction in transactions:
            if transaction.is_deposit():  
                self._account_treeview.insert(selected_item, 'end', values=("", str(transaction)), tags=("deposit",))
            else:
                self._account_treeview.insert(selected_item, 'end', values=("", str(transaction)), tags=("withdrawal",))

        if not transactions:
            self._account_treeview.insert(selected_item, 'end', values=("", "No transaction history."), tags=("withdrawal",))

    


    def _add_account(self,session):
        new_account_window = OpenAccount(self._window)
        account_type = new_account_window.get_account_type()
        
        if account_type:
            try:
                self._bank.add_account(account_type, self._session)

                self._session.commit()
                logging.debug("Saved to bank.db")
            except Exception as e:  
                    print(f"An error occurred: {e}")  

        self.populate_treeview(self._session)


    def _add_transaction(self):
        selected_item = self._account_treeview.focus()
        if not selected_item:  
            messagebox.showwarning("Warning", "Please select an account first!")
            return
        else:
            account = self.get_account(selected_item)
            transactions = account.get_transactions()
            balance = account.get_balance()
            last_transaction_date = None  

            if transactions: 
                last_transaction_date = transactions[-1].date  

            transaction_window = AddTransaction(self._window, last_transaction_date, balance)

            transaction_amount, transaction_date = transaction_window.get_transaction_details()

            if transaction_amount is not None and transaction_date is not None:
                try:
                    account.add_transaction(self._session, transaction_amount, transaction_date) 
                
                    logging.debug("Saved to bank.db")

                except TransactionLimitError as ex:
                    warning_message = f"This transaction could not be completed because this account already has {ex.limit} transactions in this {ex.limit_type}."
                    messagebox.showwarning("Transaction Limit Reached", warning_message)
                    self._session.rollback()

                self._session.commit()
                self.populate_treeview(self._session)


    def get_account(self,selected):
        """Method to get the relevant account information from account number.
        Takes in an integer and returns the account information related to the number."""
        account_info = self._account_treeview.item(selected, 'values')[0]
        _, account_part = account_info.split("#")
        account_number, _ = account_part.strip().split(",", 1)
        account_number = account_number.lstrip('0')
        return self._bank.get_account(self._session, int(account_number))
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """
        Handle uncaught exceptions by displaying a user-friendly message
        and logging the technical details.
        """
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

        error_message = "Sorry! Something unexpected happened. If this problem persists, please contact our support team for assistance."

        messagebox.showerror("Error", error_message)

        sys.exit(1)


    def _add_interest(self):
        selected_item = self._account_treeview.focus()
        if not selected_item:  
            messagebox.showwarning("Warning", "Please select an account first!")
            return  

        account = self.get_account(selected_item)
        
        if not account.get_transactions():
            messagebox.showwarning("Warning", "There are no transactions on this account. Please make at least one transaction before assessing interest and fees.")
            return  

        try:
            account.assess_interest_and_fees(self._session)  
            self.populate_treeview(self._session)  
            logging.debug("Triggered interest and fees")
            logging.debug("Saved to bank.db")

        except TransactionSequenceError as e:
            
            messagebox.showwarning(
                "Transaction Error",
                f"Cannot apply interest and fees again in the month of {e.latest_date.strftime('%B')}."
            )
        except Exception as e: 
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            logging.error(f"An error occurred: {str(e)}")



# Execute the GUI
if __name__ == "__main__":
    try:
        engine = sqlalchemy.create_engine("sqlite:///bank.db")  
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine) 
        
        BankAppGUI()


    except Exception as e:
        BankAppGUI.handle_exception(type(e), e, e.__traceback__)
