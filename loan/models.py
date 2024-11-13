from django.db import models

# Siplify samples
class LoanInput(models.Model):
    loan_number = models.IntegerField(unique=True)
    loan_amount = models.FloatField()
    interest_rate = models.FloatField()
    start_date = models.DateField()
    term = models.IntegerField()
    payment_frequency = models.CharField(max_length=20)
    cpr = models.FloatField()

    def __str__(self):
        return f"{self.loan_number}"

# For Modified Sample
class LoanTape(models.Model):
    start_date = models.DateField()
    original_principal = models.FloatField()
    amortization_term_month = models.IntegerField()
    mortgage_term_month = models.IntegerField()
    interest_rate = models.FloatField()
    compounding_frequency = models.CharField(max_length=20)
    payment_frequency = models.CharField(max_length=20)
    cpr = models.FloatField()