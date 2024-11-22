import pandas as pd
from .models import LoanInput, LoanTape
from commons.helpers import (
    prepare_calculated_loan_details, 
    create_amortization_schedule, 
    conver_file_to_dataframe,
    prepare_modified_calculated_loan_details,
    create_periodic_amortization,
    convert_to_daily_amortization,
    convert_to_monthly_amortization
)

class Simplify():
    
    def __init__(self) -> None:
        pass
    
    

class Modifiy():
    
    def __init__(self) -> None:
        pass
    
    
class LoansTape():
    
    def __init__(self) -> None:
        pass
    
    
    def get_simplified_loan_list(self):
        loans = LoanInput.objects.all().values('loan_number', 'loan_amount', 
                                                'interest_rate', 'start_date',
                                                'term', 'payment_frequency', 'cpr',)
        
        return prepare_calculated_loan_details(loans)
        
    
    def get_simplified_loan_by_loan_number(self, df, loan_number):
        
        loan_number = int(loan_number)
        
        # Filter by loan number and display the amortization scheduler
        loan_info = df[df['loan_number'] == loan_number]
        label = f"No Information for Loan Number {loan_number}"
        
        if not loan_info.empty:
            label = "Amortization Schedule"
            
            # Amortization Schedule
            df =  create_amortization_schedule(loan_info)
        
        return df, label
    
    def get_consolidated_simplified_loans(self, df, date=None):
        
        loans_list = []
        for index, d in df.iterrows():
            loans_list.append(create_amortization_schedule(pd.DataFrame([d]))
        )
        
        df = pd.concat(loans_list)
        
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.drop('Period', axis=1)
        df['Date'] = df['Date'].dt.strftime('%Y/%d/%m')
        df = df.groupby('Date').agg({'Principal Remaining':'sum','Payment':'sum',
                                                'Prepayment':'sum','Interest':'sum', 
                                                'Principal': 'sum', 'Closing Ballance': 'sum'}).reset_index()
        
        # NOTE: If date is given, filters dataframe by date
        if date:
            date_obj = date.split('-')
            year = date_obj[0]
            month = date_obj[1]
            day = date_obj[2]
            date = f"{year}/{month}/{day}"
            df = df[df['Date'] == date]

        return df 
    
    
    def get_modified_loan_list(self):
        loans = LoanTape.objects.all().values('start_date', 'original_principal', 
                                                'amortization_term_month', 'mortgage_term_month',
                                                'interest_rate', 'compounding_frequency', 
                                                'payment_frequency', 'cpr',)
        
        return pd.DataFrame(list(loans))
    
    
    def get_modified_loan_by_id(self, df, loan_number):
        loan_number = int(loan_number)
        
        # Filter by loan number and display the amortization scheduler
        loan_info = df.iloc[loan_number - 1]
        label = f"No Information for Loan Number {loan_number}"
        
        if not loan_info.empty:
            label = "Amortization Information"
            
            loans_df, details_df = prepare_modified_calculated_loan_details(loan_info)
            
        return loans_df, details_df, label
    
    
    def create_periodic_amortization(self, loans_df, details_df):
        return create_periodic_amortization(loans_df, details_df)
    
    def download_amortization_schedule(self, loan_id):
        
        loans = self.get_modified_loan_list()
        loans_df, details_df, label= self.get_modified_loan_by_id(loans, loan_id)
        periodic_df = self.create_periodic_amortization(loans_df, details_df)
        
        daily_df = convert_to_daily_amortization(periodic_df)
        monthly_df = convert_to_monthly_amortization(loans_df, details_df)

        return periodic_df, daily_df, monthly_df
        
    
    def upload_simplify_file(self, file):
        
        file.seek(0)
    
        df = conver_file_to_dataframe(file)

        for index, row in df.iterrows():
            obj = LoanInput(
                            loan_number=row['loan number'],
                            loan_amount=row['loan amount'],
                            interest_rate=row['interest_rate'],
                            start_date=row['start_date'],
                            term=row['term '],
                            payment_frequency=row['payment frequency'],
                            cpr=row['CPR (Conditional Prepayment Rate)']
                            )
            
            obj.save()
        
    
    def upload_modified_file(self, file):
        file.seek(0)
    
        df = conver_file_to_dataframe(file)

        for index, row in df.iterrows():
            obj = LoanTape(
                            start_date=row['start_date'],
                            original_principal=row['original_principal'],
                            amortization_term_month=row['amortization_term_months'],
                            mortgage_term_month=row['mortgage_term_months'],
                            interest_rate=row['interest_rate'],
                            compounding_frequency = row['compounding_frequency'],
                            payment_frequency=row['payment_frequency'],
                            cpr=row['cpr']
                            )
            
            obj.save()