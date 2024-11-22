import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect, HttpResponse
from .forms import FileUploadForm, FilterLoanForm
from .models import LoanInput, LoanTape
from loan.loans_lib import LoansTape
from commons.helpers import (
    prepare_calculated_loan_details, 
    create_amortization_schedule, 
    conver_file_to_dataframe,
    prepare_modified_calculated_loan_details,
    create_periodic_amortization
)

lt = LoansTape()

def upload_file(request):
    
    upload_type = request.POST.get('type')
    form = FileUploadForm()
    
    if request.method == "POST" and request.FILES['file']:
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():

            file = request.FILES['file']
            
            if upload_type == '1':
                
                lt.upload_simplify_file(file)
        
            if upload_type == '2':
                lt.upload_modified_file(file)
            
            #return redirect("/loans/upload")
    
    return render(request, 'loan/upload_file.html', {'form': form})


def filter_loans(request):
    '''
    Returns list of Simplify Loans and filter Loans based on user input
    loan_number: if loan in request return amortization schedule of specific loan number
    consolidate: if in request return consolidated dataframes of all loans grouped by date
    '''
    
    label = "Loan Information"
    form = FilterLoanForm()
    loan_number = request.POST.get("loan_number")
    consolidate = request.POST.get("consolidate")
    date = request.POST.get('date')
    loan_type = request.POST.get('type')
    details_html = ''
    periodic_html = ''
    loans_html = ''
    
    if loan_type == '1':
        # Retrieve list of all Loans and convert to Pandas Dataframe
        loans_df = lt.get_simplified_loan_list()

        if loan_number: 
            loans_df, label = lt.get_simplified_loan_by_loan_number(loans_df, loan_number)
    
        # Return the consolidated dataframes for all loans
        if consolidate == 'on':
            
            loans_df = lt.get_consolidated_simplified_loans(loans_df, date=date)
            
        
        loans_html = loans_df.to_html(index=False,
                                            col_space=120,
                                            float_format="{:,.2f}".format,
                                            justify="center",
                                            classes='table table-striped table-hover table-responsive')
    
    if loan_type == '2':
        # Retrieve list of all Loans and convert to Pandas Dataframe
        loans_df = lt.get_modified_loan_list()
        
        if loan_number: 
            loans_df, details_df, label= lt.get_modified_loan_by_id(loans_df, loan_number)
            
            details_html = details_df.to_html(index=False,
                                col_space=120,
                                float_format="{:,.2f}".format,
                                justify="center",
                                classes='table table-striped table-hover table-responsive')

            periodic_df = lt.create_periodic_amortization(loans_df, details_df)
            periodic_html = periodic_df.to_html(index=False,
                                col_space=120,
                                float_format="{:,.2f}".format,
                                justify="center",
                                classes='table table-striped table-hover')
                
        loans_html = loans_df.to_html(index=False,
                                    col_space=120,
                                    float_format="{:,.2f}".format,
                                    justify="center",
                                    classes='table table-striped table-hover table-responsive')
    
    
    return render(request, 'loan/simplified_loan.html', {'form': form, 'loans': loans_html,
                                                         'details': details_html, 
                                                         'periodic': periodic_html, 
                                                         'loan_number': loan_number , 'label': label})


def download_loan_schedule(request, loan_id):
    
    periodic_df, daily_df, monthly_df = lt.download_amortization_schedule(loan_id)
    
    # Get the current timestamp for filename
    current_timestamp = datetime.now()
    timestamp_str = current_timestamp.strftime('%Y%m%d%H%M%S')
    file_name = f"modified_loans_{timestamp_str}"
    # Create a response object to return the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{file_name}.xlsx"'
    
    # Use pandas to write the DataFrame to an Excel file
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        periodic_df.to_excel(writer, index=False, sheet_name='periodic')
        daily_df.to_excel(writer, index=False, sheet_name='daily')
        monthly_df.to_excel(writer, index=False, sheet_name='monthly')
        
    return response
