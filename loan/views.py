import pandas as pd
from django.shortcuts import render, redirect, HttpResponse
from .forms import FileUploadForm, FilterLoanForm
from .models import LoanInput, LoanTape
from commons.helpers import prepare_calculated_loan_details, create_amortization_schedule

# Create your views here.
def handle_simplify_uploadedd_file(file):
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



def conver_file_to_dataframe(file):
    file_ext = str(file).split(".")[-1]
    if file_ext == "xlsx":
        df = pd.read_excel(file)
    
    if file_ext == "csv":
        df = pd.read_csv(file)

    return df
    # df = df[1:]
    # df.to_excel(str(file), index=False)
    

def upload_file(request):
    '''
    
    '''
    print("REQ TYPE:", request.POST.get('type'))
    if request.method == "POST" and request.FILES['file']:
        form = FileUploadForm(request.POST, request.FILES)

        if form.is_valid():

            file = request.FILES['file']
        
            #handle_simplify_uploadedd_file(file)

            return redirect("/loans/upload")
    else:
        form = FileUploadForm()
    
    return render(request, 'loan/upload_file.html', {'form': form})

def filter_loans(request):
    label = "Loan Information"
    form = FilterLoanForm()
    loan_number = request.POST.get("loan_number")
    consolidate = request.POST.get("consolidate")
    date = request.POST.get('date')

    # Retrieve list of all Loans and convert to Pandas Dataframe
    loans = LoanInput.objects.all().values('loan_number', 'loan_amount', 
                                            'interest_rate', 'start_date',
                                            'term', 'payment_frequency', 'cpr',)
    loans_df = prepare_calculated_loan_details(loans)

    print(type(request.POST.get('date')))
    if loan_number:
        loan_number = int(loan_number)
        # Filter by loan number and display the amortization scheduler
        loan_info = loans_df[loans_df['loan_number'] == loan_number]
        label = f"No Information for Loan Number {loan_number}"
        print("INFO: ", type(loan_info))
        if not loan_info.empty:
            label = "Amortization Schedule"

            # Amortization Schedule
            loans_df =  create_amortization_schedule(loan_info)
    
    if consolidate == 'on':
        loans_list = []
        for index, df in loans_df.iterrows():
            loans_list.append(create_amortization_schedule(pd.DataFrame([df]))
        )
        
        loans_df = pd.concat(loans_list)
        print(loans_df.columns)
        loans_df['Date'] = pd.to_datetime(loans_df['Date'])
        loans_df = loans_df.drop('Period', axis=1)
        loans_df['Date'] = loans_df['Date'].dt.strftime('%Y/%d/%m')
        loans_df = loans_df.groupby('Date').agg({'Principal Remaining':'sum','Payment':'sum',
                                                 'Prepayment':'sum','Interest':'sum', 
                                                 'Principal': 'sum', 'Closing Ballance': 'sum'}).reset_index()
        # sum().reset_index().sort_values("Date")
        

    if date:
        date_obj = date.split('-')
        year = date_obj[0]
        month = date_obj[1]
        day = date_obj[2]
        date = f"{year}/{month}/{day}"
        print(date)
        print(loans_df['Date'])
        
        loans_df = loans_df[loans_df['Date'] == date]

            
 
    loans_html = loans_df.to_html(index=False,
                                  col_space=120,
                                  float_format="{:,.2f}".format,
                                  justify="center",
                                  classes='table table-striped table-hover')
    
    return render(request, 'loan/filter_loan.html', {'form': form, 'loans': loans_html, 'label': label})
