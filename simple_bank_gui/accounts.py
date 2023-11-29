import logging
from decimal import Decimal
from exceptions import OverdrawError, TransactionLimitError, TransactionSequenceError
from transactions import Transaction
from base import Base 

from sqlalchemy import Column, Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship, backref

class Account(Base):
    """This is an abstract class for accounts.  Provides default functionality for adding transactions, getting balances, and assessing interest and fees.  
    Accounts should be instantiated as SavingsAccounts or CheckingAccounts
    """
    __tablename__ = 'accounts'

    _account_number = Column(Integer, primary_key=True)  
    _type = Column(String)
    _interest_rate = Column(Numeric)
    _transactions = relationship("Transaction", backref=backref('accounts'))

    _bank_id = Column(Integer, ForeignKey('bank._id'))

    __mapper_args__ = {
        'polymorphic_identity':'account',
        'polymorphic_on': _type
    }

    def _get_acct_num(self):
        return self._account_number

    account_number = property(_get_acct_num)

    def add_transaction(self, session, amt, date, exempt=False):
        """Creates a new transaction and checks to see if it is allowed, adding it to the account if it is.

        Args:
            amt (Decimal): amount for new transaction
            date (Date): Date for the new transaction.
            exempt (bool, optional): Determines whether the transaction is exempt from account limits. Defaults to False.
        """

        t = Transaction(
            amt=amt,
            acct_num=self._account_number,  
            date=date, 
            exempt=exempt
        )

        if not t.is_exempt():
            self._check_balance(t)
            self._check_limits(t)
            self._check_date(t)
        session.add(t)
        session.commit()

    def _check_balance(self, transaction):
        """
        Checks whether the incoming transaction would overdraw the account by directly querying
        the database for the current balance and comparing it to the transaction amount.

        Args:
            transaction (Transaction): The pending transaction to check.

        Raises:
            OverdrawError: If the transaction would overdraw the account.
        """
        if not transaction.check_balance(self.get_balance()):
            raise OverdrawError()

    def _check_limits(self, t):
        pass

    def _check_date(self, new_transaction):
        """
        Verifies that the incoming transaction is not dated before the latest transaction
        in the account.

        Args:
            new_transaction (Transaction): The new transaction to be added.

        Raises:
            TransactionSequenceError: If the new transaction is older than the most recent transaction.
        """
        if len(self._transactions) > 0:
            latest_transaction = max(self._transactions)
            if new_transaction < latest_transaction:
                raise TransactionSequenceError(latest_transaction.date)

    def get_balance(self):
        """
        Gets the balance for an account by summing its transactions.

        Returns:
            Decimal: current balance.
        """
        return sum(self._transactions)

    def _assess_interest(self, session, latest_transaction):
        """Calculates interest for an account balance and adds it as a new transaction exempt from limits.
        """
        self.add_transaction(session, self.get_balance() * self._interest_rate, 
                        date=latest_transaction.last_day_of_month(), 
                        exempt=True)
        

    def _assess_fees(self, session, latest_transaction):
        pass


    def assess_interest_and_fees(self,session):
        """Used to apply interest and/or fees for this account

        Raises:
            TransactionSequenceError: Indicates that the new transactions were
            not newer than the most recent interest or fees transactions
        """
        latest_transaction = max(self._transactions)
        for t in self._transactions:
            if t.is_exempt() and t.in_same_month(latest_transaction):
                # found an interest or fee transaction that is already in the
                # same month as the most recent transaction
                raise TransactionSequenceError(t.date)
        self._assess_interest(session,latest_transaction)
        self._assess_fees(session,latest_transaction)

    def __str__(self):
        """Formats the account number and balance of the account.
        For example, '#000000001,<tab>balance: $50.00'
        """
        return f"#{self._account_number:09},\tbalance: ${self.get_balance():,.2f}"

    def get_transactions(self):
        "Returns sorted list of transactions on this account"
        return sorted(self._transactions)
    
    @account_number.setter
    def account_number(self, value):
        self._account_number = value


class SavingsAccount(Account):
    """Concrete Account class with daily and monthly account limits and high interest rate.
    """
    __tablename__ = 'savingsaccounts'
    
    _account_number = Column(Integer, ForeignKey('accounts._account_number'), primary_key=True)

    _daily_limit = Column(Integer)
    _monthly_limit = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'savings', 
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._interest_rate = Decimal("0.0041")
        self._daily_limit = 2
        self._monthly_limit = 5

    def _check_limits(self, t1):
        """determines if the incoming trasaction is within the accounts transaction limits

        Args:
            t1 (Transaction): pending transaction to be checked

        Returns:
            bool: true if within limits and false if beyond limits
        """
        # Count number of non-exempt transactions on the same day as t1
        num_today = len(
            [t2 for t2 in self._transactions if not t2.is_exempt() and t2.in_same_day(t1)])
        # Count number of non-exempt transactions in the same month as t1
        num_this_month = len(
            [t2 for t2 in self._transactions if not t2.is_exempt() and t2.in_same_month(t1)])
        # check counts against daily and monthly limits
        if num_today >= self._daily_limit:
            raise TransactionLimitError("day", self._daily_limit)
        if num_this_month >= self._monthly_limit:
            raise TransactionLimitError("month", self._monthly_limit)

    def __str__(self):
        """Formats the type, account number, and balance of the account.
        For example, 'Savings#000000001,<tab>balance: $50.00'
        """
        return "Savings" + super().__str__()


class CheckingAccount(Account):
    """Concrete Account class with lower interest rate and low balance fees.
    """
    _account_number = Column(Integer, ForeignKey("accounts._account_number"), primary_key=True)
    __tablename__ = 'checkingaccount'
    _balance_threshold = Column(Numeric)
    _low_balance_fee = Column(Numeric)

    __mapper_args__ = {
        'polymorphic_identity':'checking',
    }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._interest_rate = Decimal("0.0008")
        self._balance_threshold = 100    
        self._low_balance_fee = Decimal("-5.44")

    def _assess_fees(self, session, latest_transaction):
        """Adds a low balance fee if balance is below a particular threshold. Fee amount and balance threshold are defined on the CheckingAccount.
        """
        if self.get_balance() < self._balance_threshold:
            self.add_transaction(session, self._low_balance_fee,
                                 date=latest_transaction.last_day_of_month(), 
                                 exempt=True)

    def __str__(self):
        """Formats the type, account number, and balance of the account.
        For example, 'Checking#000000001,<tab>balance: $50.00'
        """
        return "Checking" + super().__str__()