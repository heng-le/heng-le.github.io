from accounts import SavingsAccount, CheckingAccount
from base import Base
import logging
from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.orm import relationship, backref
from accounts import Account
SAVINGS = "savings"
CHECKING = "checking"

logging.basicConfig(filename='bank.log', level=logging.DEBUG,
                    format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class Bank(Base):
    __tablename__ = 'bank'

    _id = Column(Integer, primary_key=True)  
    _accounts = relationship("Account", backref=backref('bank'))

    def __init__(self):
        self._accounts = []

    def add_account(self, acct_type, session):
        """Creates a new Account object and adds it to this bank object.

        Args:
            acct_type (string): "savings" or "checking" to indicate the type of account to create
            session (Session): The SQLAlchemy session for database operations.
        """
        acct_num = self._generate_account_number(session) 

        if acct_type == SAVINGS:
            account = SavingsAccount(account_number=acct_num)
        elif acct_type == CHECKING:
            account = CheckingAccount(account_number=acct_num)
        else:
            raise ValueError("Invalid account type specified") 

        session.add(account)
        self._accounts.append(account) 
        session.commit()  
        logging.debug(f"Created account: {account._account_number}") 



    
    def _generate_account_number(self, session):
        return session.query(Account).count() + 1

    def show_accounts(self):
        "Accessor method to return accounts"
        return self._accounts

    def get_account(self, session, account_num):
        """Fetches an account by its account number.

        Args:
            session (Session): The SQLAlchemy session for database operations.
            account_num (int): Account number to search for.

        Returns:
            Account: matching account or None if not found
        """
        account = session.query(Account).filter(Account._account_number == account_num).first()

        return account