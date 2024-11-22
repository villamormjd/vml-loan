from amortization.amount import calculate_amortization_amount
from amortization.enums import PaymentFrequency
from tabulate import tabulate
import numpy_financial as npf
from typing import Iterator, Tuple
from datetime import date
from dateutil.relativedelta import relativedelta

import pandas as pd
from datetime import date, datetime, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY

principal = 10000
rate = 5/100
period = 360
frequency = PaymentFrequency.MONTHLY
smm = .83/ 100
renewal_period = 12
start_date =  date(2023, 1, 13)

# amount = calculate_amortization_amount(principal, rate, period, frequency)
# print(amount)

#p = round(-(npf.pmt((.192 / 100) / 12, 780, principal).tolist()),2)
# print(p)

#print([i for i in table])
#calculate_amortization_amount(principal, rate, 1560, payment_frequency=frequency)

# adjusted_interest = interest_rate / payment_frequency.value
# x = (1 + adjusted_interest) ** period
# return round(principal * (adjusted_interest * x) / (x - 1), 2)

# 5292-2010-0954
# BDO-2553737-N3D2F5
# 48684.24

def get_next_schedule_date(start_date):

    new_date = start_date + relativedelta(months=1)
    new_date_str = new_date.strftime("%d/%m/%Y")

    dr = rrule(WEEKLY, dtstart=start_date, count=24, interval=2)
    return new_date_str, new_date
    

def amortization_schedule(
    principal: float, interest_rate: float, period: int, start_date: date,  payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
) -> Iterator[Tuple[int, float, float, float, float]]:
    """
    Generates amortization schedule

    :param principal: Principal amount
    :param interest_rate: Interest rate per year
    :param period: Total number of periods
    :param payment_frequency: Payment frequency per year
    :return: Rows containing period, amount, interest, principal, balance, etc
    """
    amortization_amount =  calculate_amortization_amount(principal, rate, period, payment_frequency=frequency)
    payment = amortization_amount
    adjusted_interest = interest_rate / payment_frequency.value
    balance = principal
    
    for number in range(1, period + 1):
        interest = round(balance * adjusted_interest, 2)
        opening_balance = balance
        if balance > 0:
            next_schedule_str, next_schedule  = get_next_schedule_date(start_date)
            amortization_amount = min(amortization_amount, opening_balance)
            prepayment = 0 if payment  > amortization_amount else balance * smm
            principal = amortization_amount - interest if opening_balance > amortization_amount else opening_balance
            principal_amount = (principal + prepayment)
            balance -= principal_amount
            payment = min(amortization_amount, (principal + interest))
            maturity = 0 if number != renewal_period else balance 
            start_date = next_schedule
            

            yield number, next_schedule_str, opening_balance, amortization_amount, interest, prepayment, principal_amount, balance, maturity


table = (x for x in amortization_schedule(principal, rate, period, start_date, payment_frequency=frequency))

# print(
#     tabulate(
#         table,
#         headers=["Number", "Opening Balance",  "Amount", "Interest", "Prepayment" , "Principal", "Closing Balance", "Maturity"],
#         floatfmt=",.2f",
#         numalign="right"
#     )
# )

t = list(table)
f = [0, '13/01/2023', 0, 0, 0, 0, 0, principal, 0 ]
t.insert(0, f)
# print(t)

import pandas as pd
df = pd.DataFrame(t, columns=["Period", "Date", "Opening Balance",  "Amount", "Interest", "Prepayment" , "Principal", "Closing Balance", "Maturity"])
df['Principal'] = df['Principal'] - df['Prepayment']
print(df.head(renewal_period + 1))


import pandas as pd
from datetime import datetime, timedelta

# Function to create the daily amortization schedule
def convert_to_daily_amortization(df):
    # List to hold the transformed rows
    daily_schedule = []
    
    # Start date of the first period
    start_date = datetime.strptime(df["Date"].values[0], "%d/%m/%Y")
    
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
        for day in range(32):  # assuming a 30-day period for simplicity; adjust based on real periods
            date = start_date + timedelta(days=day)
            
            # Day of the month
            day_of_month = date.day
            
            # Calculate Year-Month format (e.g., '2024-01')
            year_month = date.strftime("%Y-%m")
            
            # Calculate closing balance after applying principal and prepayment (after the last period)
            if day == 31:  # last day of this period
                closing_balance = opening_balance - (principal + prepayment)

            # Calculate maturity for the last day
            maturity = 0 if closing_balance <= 0 else closing_balance
            
            # Create a daily entry for the amortization schedule
            if day == 31:
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
                'payment': amount if day == 31 else 0,  # only show payment on last day of the period
                'interest': interest if day == 31 else 0,  # interest only on last day
                'principal': principal if day == 31 else 0,  # principal only on last day
                'prepayment': prepayment if day == 31 else 0,  # prepayment only on last day
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

# Example input dataframe (based on the provided structure)
# data = {
#     'Period': [0, 1],
#     'Date': ['13/01/2023', '13/02/2023'],
#     'Opening Balance': [0, 10000.0],
#     'Amount': [0.00, 58.46],
#     'Interest': [0.00, 41.67],
#     'Prepayment': [0.0, 83.00],
#     'Principal': [0.00, 16.79],
#     'Closing Balance': [10000.0, 9900.21],
#     'Maturity': [0.00, 0.00]
# }

# df = pd.DataFrame(data)

# Call the conversion function
daily_amortization_df = convert_to_daily_amortization(df.head(renewal_period))

# Display the result
#print(daily_amortization_df.head(35))
