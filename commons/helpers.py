import pandas as pd
import numpy as np
import numpy_financial as npf
from dateutil.relativedelta import relativedelta
import datetime
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY

def prepare_calculated_loan_details(loans):

    loans_df = pd.DataFrame.from_records(loans)
    
    loans_df['interest_rate'] = loans_df['interest_rate'] * 100
    loans_df['cpr'] = loans_df['cpr'] * 100

    apr = (loans_df['interest_rate'] / 100) / 12
    term = loans_df['term']
    amount = loans_df['loan_amount']
    cpr = loans_df['cpr'] / 100
    
    loans_df['monthly_interest_rate'] = round(loans_df['interest_rate'] / 12, 2)
    loans_df['pmt'] = np.round(-npf.pmt( apr, term, amount), 2)
    loans_df['smm'] = np.round((1-(pow((1-cpr), 1/12))) * 100, 2)

    return loans_df


def make_payment(period, principal, pmt, mpr, smm, rate, start_date, interval):
    '''Makes a 'payment' by subtracting and updated payment amount from the
    principal. Returns the principal remaining, and the amount of principal and interest paid
    '''
    closing_bal = principal
    current_interest_payment = principal * mpr
    payment = min(pmt, (principal + current_interest_payment))
    prepayment = 0 if payment < pmt else closing_bal * smm
    current_principal_payment = (payment + prepayment) - current_interest_payment
    principal -= current_principal_payment
    period += 1
    
    new_date_str = get_next_schedule_date(start_date, interval)

    return [period,
            new_date_str,
            round(closing_bal, 2),
            payment,
            prepayment,
            rate,
            round(mpr * 100,2),
            round(current_interest_payment, 2),
            round(current_principal_payment, 2), 
            round(principal, 2)] 


def create_amortization_schedule(loan_info):
    '''Returns an Amortization Table in the form of a DataFrame
    '''
    principal = loan_info['loan_amount'].values[0]
    term_remaining = loan_info['term'].values[0]
    pmt = loan_info['pmt'].values[0]
    mpr = loan_info['monthly_interest_rate'].values[0] / 100
    smm = loan_info['smm'].values[0] / 100
    rate = loan_info['interest_rate'].values[0]
    start_date = loan_info['start_date'].values[0].strftime("%d/%m/%Y")
    interval = loan_info['payment_frequency'].values[0].lower()

    # Period 0 data
    payments = [[0, start_date, 0, 0, 0, 0, 0, 0, 0, principal]]
    total_interest = 0
    period = 0
    
    while principal > 0 and term_remaining > 0:
        payment = make_payment(period, principal, pmt, mpr, smm, rate, start_date, interval)
        period=payment[0]
        principal = payment[-1]
        start_date = payment[1]
        term_remaining -= 1
        total_interest += payment[2]
        payments.append(payment)

    amortization_table = pd.DataFrame(data=payments,
                                        columns=["Period",
                                                 "Date",
                                                "Principal Remaining",
                                                "Payment", 
                                                "Prepayment", 
                                                "Interest Rate",
                                                "Monthly Interest Rate",
                                                "Interest",
                                                "Principal",
                                                "Closing Ballance"])
        
    return amortization_table

def get_next_schedule_date(start_date: str, interval):
    new_date = datetime.datetime.strptime(start_date, "%d/%m/%Y").date()
    new_date_str = new_date.strftime("%d/%m/%Y")

    new_date_str = generate_dates(new_date_str, interval=interval)
    return new_date_str

def generate_dates(start_date, interval='daily'):
    """
    Generate dates based on a starting date and interval type (daily or bi-weekly).
    
    Parameters:
    - start_date: The initial date to start the period (in 'YYYY-MM-DD' format).
    - num_periods: The number of periods (for daily or bi-weekly) to generate. Optional if `end_date` is provided.
    - end_date: The final date to stop generating dates. Optional if `num_periods` is provided.
    - interval: The interval type - 'daily' or 'bi-weekly'. Default is 'daily'.

    Returns:
    - A list of generated dates.
    """
    # Convert the start date from string to a datetime object
    start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y").date()
    current_date = start_date

    if interval == 'daily':
        # Generate next daily date from start date
        current_date += datetime.timedelta(days=1)

    elif interval == 'bi-weekly':
        # Generate bi-weekly date from start date
        current_date += datetime.timedelta(weeks=2)
    
    elif interval == 'monthly':
        # Generate monthly date from start date
        current_date += relativedelta(months=1)
        
    else:
        raise ValueError("Invalid interval. Please choose either 'daily', 'bi-weekly', or 'monthly'.")
    
    return current_date.strftime("%d/%m/%Y")
    

