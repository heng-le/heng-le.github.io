import sys
import pickle
import logging
from decimal import Decimal, setcontext, BasicContext, InvalidOperation
from datetime import datetime
from base import Base
from bank import Bank
from exceptions import OverdrawError, TransactionLimitError, TransactionSequenceError

import sqlalchemy
from sqlalchemy.orm.session import sessionmaker

# context with ROUND_HALF_UP
setcontext(BasicContext)

logging.basicConfig(filename='bank.log', level=logging.DEBUG,
                    format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class BankCLI():
    """Driver class for a command-line REPL interface to the Bank application"""

    def __init__(self):
        self._session = Session()
        self._bank = Bank()

        # Attempt to retrieve the bank instance from the database
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
        # establishes relationship to Accounts

        self._selected_account = None

        self._choices = {
            "1": self._open_account,
            "2": self._summary,
            "3": self._select,
            "4": self._add_transaction,
            "5": self._list_transactions,
            "6": self._monthly_triggers,
            "7": self._quit,
        }

    def _display_menu(self):
        print(f"""--------------------------------
Currently selected account: {self._selected_account}
Enter command
1: open account
2: summary
3: select account
4: add transaction
5: list transactions
6: interest and fees
7: quit""")

    def run(self):
        """Display the menu and respond to choices."""
        while True:
            self._display_menu()
            choice = input(">")
            action = self._choices.get(choice)
            # expecting a digit 1-7
            if action:
                action()
            else:
                # not officially part of spec since we don't give invalid options
                print("{0} is not a valid choice".format(choice))

    def _summary(self):
        # Assuming the Bank model has a method to retrieve all accounts.
        accounts = self._bank.show_accounts()
        for account in accounts:
            print(str(account))

    def _quit(self):
        self._session.close()
        sys.exit(0)

    def _add_transaction(self):
        if self._selected_account is None:
            print("Please select an account first.")
            return

        amount = None
        while amount is None:
            try:
                amount = Decimal(input("Amount?\n>"))
            except InvalidOperation:
                print("Please try again with a valid dollar amount.")

        date = None
        while date is None:
            try:
                date_str = input("Date? (YYYY-MM-DD)\n>")
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print("Please try again with a valid date in the format YYYY-MM-DD.")

        # Attempt to add the transaction.
        try:

            self._selected_account.add_transaction(self._session, amount, date) 
            logging.debug("Saved to bank.db")
        except AttributeError:
            print("This command requires that you first select an account.")
        except OverdrawError:
            print("This transaction could not be completed due to an insufficient account balance.")
            self._session.rollback()
        except TransactionLimitError as ex:
            print(f"This transaction could not be completed because this account already has {ex.limit} transactions in this {ex.limit_type}.")
            self._session.rollback()
        except TransactionSequenceError as ex:
            print(f"New transactions must be from {ex.latest_date} onward.")
            self._session.rollback()
        except Exception as e:  
            print(f"An error occurred: {e}")
            self._session.rollback()


    def _open_account(self):
        while True:  
            acct_type = input("Type of account? (checking/savings)\n>").lower()

            if acct_type in ('checking', 'savings'):
                try:
                    self._bank.add_account(acct_type, self._session)

                    self._session.commit()
                    logging.debug("Saved to bank.db")
                    break  
                except Exception as e:  
                    print(f"An error occurred: {e}")  
            else:
                break




    def _select(self):
        num = int(input("Enter account number\n>"))
        self._selected_account = self._bank.get_account(self._session, num) 

    def _monthly_triggers(self):
        try:
            self._selected_account.assess_interest_and_fees(self._session)
            logging.debug("Triggered interest and fees")
            logging.debug("Saved to bank.db")
        except AttributeError:
            print("This command requires that you first select an account.")
        except TransactionSequenceError as e:
            print(
                f"Cannot apply interest and fees again in the month of {e.latest_date.strftime('%B')}.")

    def _list_transactions(self):
        try:
            for t in self._selected_account.get_transactions():
                print(t)
        except AttributeError:
            print("This command requires that you first select an account.")


if __name__ == "__main__":
    try:
        engine = sqlalchemy.create_engine("sqlite:///bank.db")  
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine) 
        BankCLI().run()
    except Exception as e:
        print("Sorry! Something unexpected happened. Check the logs or contact the developer for assistance.")
        logging.error(str(e.__class__.__name__) + ": " + str(e))