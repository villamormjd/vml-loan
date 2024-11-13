from django import forms

class FileUploadForm(forms.Form):
    CHOICES = [
        ('1', 'Simplified Sample'),
        ('2', 'Modified Sample'),
    ]
    
    type = forms.ChoiceField(
        label='Sample Type',
        widget=forms.RadioSelect,
        choices=CHOICES, 
    )

    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm', 'type': 'file', 'id': 'customFile'}))
    file.form_class = 'form-group'

class FilterLoanForm(forms.Form):

    loan_number = forms.IntegerField(required=False, 
                                     widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'}))
    consolidate = forms.BooleanField(required=False)
    date = forms.DateField(required=False, widget=forms.widgets.DateInput(attrs={'type': 'date'}))
