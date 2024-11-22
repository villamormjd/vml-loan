import pandas as pd
import numpy as np
import numpy_financial as npf
import calendar
import datetime
from datetime import timedelta
from typing import Iterator, Tuple
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
from amortization.amount import calculate_amortization_amount
from .constants import CompoundFrequency, PaymentFrequency, MonthOffset, DayOffset


def conver_file_to_dataframe(file):
    '''
    Convert file into Pandas Dataframe
    '''
    file_ext = str(file).split(".")[-1]
    if file_ext == "xlsx":
        df = pd.read_excel(file)
    
    if file_ext == "csv":
        df = pd.read_csv(file)

    return df


def get_days_in_month(year, month):
    '''
    returns a tuple (weekday of first day, number of days in month)
    '''
    _, num_days = calendar.monthrange(year, month)
    return num_days


def get_next_schedule_date(start_date: str, interval):
    new_date = datetime.datetime.strptime(start_date, "%d/%m/%Y").date()
    new_date_str = new_date.strftime("%d/%m/%Y")

    new_date_str = generate_dates(new_date_str, interval=interval)
    return new_date_str


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
    '''
    Makes a 'payment' by subtracting and updated payment amount from the
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
    '''
    Returns an Amortization Table in the form of a DataFrame
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

    elif interval == 'biweekly':
        # Generate bi-weekly date from start date
        current_date += datetime.timedelta(weeks=1)
        
    elif interval == 'weekly':
        # Generate bi-weekly date from start date
        current_date += datetime.timedelta(weeks=1)
    
    elif interval == 'semimonthly':
        # Generate monthly date from start date
        current_date += relativedelta(days=15)
        
    elif interval == 'monthly':
        # Generate monthly date from start date
        current_date += relativedelta(months=1)
        
    else:
        raise ValueError("Invalid interval. Please choose either 'daily', 'bi-weekly', or 'monthly'.")
    
    return current_date.strftime("%d/%m/%Y")


def prepare_modified_calculated_loan_details(loans):
    '''
    Generate the calculated factors for modified loans
    '''
    loans_df = pd.DataFrame.from_dict([loans])
    
    compounding_frequency = loans['compounding_frequency'].replace("-","").upper()
    payment_frequency = loans['payment_frequency'].replace("-","").upper()
    
    additionalDetails = dict()
    
    additionalDetails['compounding_period'] = CompoundFrequency[compounding_frequency].value
    additionalDetails['periods_per_year'] = PaymentFrequency[payment_frequency].value
    additionalDetails['interest_rate_perpayment'] = np.round(((1+( loans['interest_rate'] / additionalDetails['compounding_period'])) ** 
                                             (additionalDetails['compounding_period'] / additionalDetails['periods_per_year']))-1, 5)
    additionalDetails['renewal_period'] = (loans['mortgage_term_month']/12) * additionalDetails['periods_per_year']
    additionalDetails['amortization_period'] = (loans['amortization_term_month']/12) * additionalDetails['compounding_period']
    additionalDetails['payment_per_period'] = np.round(-npf.pmt( (loans['interest_rate'] / 12), additionalDetails['amortization_period'], loans['original_principal']), 2)
    additionalDetails['smm'] = np.round(loans['cpr'] / additionalDetails['compounding_period'], 5)
    additionalDetails['month_offset'] = MonthOffset[payment_frequency].value
    additionalDetails['day_offset'] = DayOffset[payment_frequency].value
    
    details_df = pd.DataFrame.from_dict([additionalDetails])
    details_df['interest_rate_perpayment'] *= 100
    details_df['smm'] *= 100

    return loans_df, details_df


def amortization_schedule(loans_info: pd.DataFrame, additional_details_df: pd.DataFrame) -> Iterator[Tuple[int, float, float, float, float]]:
    """
    Generates amortization schedule
    :param principal: Principal amount
    :param interest_rate: Interest rate per year
    :param period: Total number of periods
    :param payment_frequency: Payment frequency per year
    :return: Rows containing period, amount, interest, principal, balance, etc
    """
    start_date = loans_info['start_date'].values[0].strftime("%d/%m/%Y")
    principal = loans_info['original_principal'].values[0]
    interest_rate = loans_info['interest_rate'].values[0]
    period = loans_info['amortization_term_month'].values[0]
    payment_frequency = loans_info['payment_frequency'].values[0].replace("-","")
    frequency = PaymentFrequency[payment_frequency.upper()]
    smm = additional_details_df['smm'].values[0] / 100
    renewal_period = additional_details_df['renewal_period'].values[0]
    
    
    amortization_amount =  calculate_amortization_amount(principal, interest_rate, period, payment_frequency=frequency)
    payment = amortization_amount
    adjusted_interest = interest_rate / frequency.value
    balance = principal
    
    for number in range(1, period + 1):
        interest = round(balance * adjusted_interest, 2)
        opening_balance = balance
        if balance > 0:
            next_schedule_str = get_next_schedule_date(start_date, payment_frequency.lower())
            amortization_amount = min(amortization_amount, opening_balance)
            prepayment = 0 if payment  > amortization_amount else balance * smm
            principal = amortization_amount - interest if opening_balance > amortization_amount else opening_balance
            principal_amount = (principal + prepayment)
            balance -= principal_amount
            payment = min(amortization_amount, (principal + interest))
            maturity = 0 if number != renewal_period else balance 
            start_date = next_schedule_str
            
            yield number, next_schedule_str, opening_balance, amortization_amount, interest, prepayment, principal_amount, balance, maturity
            
            
def create_periodic_amortization(loans_df, additional_details_df):
    '''
    Generate the period schedule of the loan.
    '''
    table = (x for x in amortization_schedule(loans_df, additional_details_df))
    
    t = list(table)
    f = [0, loans_df['start_date'].values[0].strftime("%d/%m/%Y"), 0, 0, 0, 0, 0, loans_df['original_principal'].values[0], 0 ]
    t.insert(0, f)
    df = pd.DataFrame(t, columns=["Period", "Date", "Opening Balance",  "Amount", "Interest", "Prepayment" , "Principal", "Closing Balance", "Maturity"])
    df['Principal'] = df['Principal'] - df['Prepayment']    
    
    return df.head(int(additional_details_df['renewal_period'].values) + 1 )


def convert_to_monthly_amortization(df, additional_df):
    df['payment_frequency'] = 'Monthly'
    return create_periodic_amortization(df, additional_df)
    

def convert_to_daily_amortization(df):
    # List to hold the transformed rows
    daily_schedule = []
    date_obj = df["Date"].values[0]
    
    # Start date of the first period
    start_date = datetime.datetime.strptime(date_obj, "%d/%m/%Y")
    days_in_month = get_days_in_month(start_date. year, start_date.month)
    
    # Iterate over each period in the original dataframe
    for idx, row in df.iterrows():
        # Period and opening balance from original dataframe
        period = row['Period']
        opening_balance = row['Opening Balance']
        
        # Payment, interest, principal, prepayment, and closing balance from the original row
        amount = row['Amount']
        interest = row['Interest']
        prepayment = row['Prepayment']
        principal = row['Principal']
        closing_balance = row['Closing Balance']
        
        # Iterate over the days in this period (start from 0, as we create daily rows)
        for day in range(days_in_month + 1):  # assuming a 30-day period for simplicity; adjust based on real periods
            date = start_date + timedelta(days=day)
            
            # Day of the month
            day_of_month = date.day
            
            # Calculate Year-Month format (e.g., '2024-01')
            year_month = date.strftime("%Y-%m")
            
            # Calculate closing balance after applying principal and prepayment (after the last period)
            if day == days_in_month:  # last day of this period
                closing_balance = opening_balance - (principal + prepayment)

            # Calculate maturity for the last day
            maturity = 0 if closing_balance <= 0 else closing_balance
            
            # Create a daily entry for the amortization schedule
            if day == days_in_month:
                index = idx + 1 if idx + 1 < len(df) else idx
                row = df.iloc[index].to_dict()
                amount = row['Amount']
                interest = row['Interest']
                prepayment = row['Prepayment']
                principal = row['Principal']
                closing_balance = row['Closing Balance']

            daily_schedule.append({
                'Period': period,
                'Day': day,
                'Year-Month': year_month,
                'date': date.strftime("%m/%d/%Y"),
                'opening_balance': opening_balance,
                'payment': amount if day == days_in_month else 0,  # only show payment on last day of the period
                'interest': interest if day == days_in_month else 0,  # interest only on last day
                'principal': principal if day == days_in_month else 0,  # principal only on last day
                'prepayment': prepayment if day == days_in_month else 0,  # prepayment only on last day
                'new_origination': 0,  # Assuming no new origination in the example
                'maturity': maturity,
                'closing_balance': closing_balance
            })
            
            # Update the opening balance for the next day (based on the amount paid)
            opening_balance = closing_balance
            
        # Move the start date to the next period
        start_date = date + timedelta(days=1)
    
    # Convert the list of daily entries to a DataFrame
    daily_df = pd.DataFrame(daily_schedule)
    
    return daily_df
