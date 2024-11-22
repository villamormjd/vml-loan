# vml-loan
Sample amortization schedule calculator or simulator.

### Setup
1. Clone repository. Create and activate virtual environment.
2. Install requirements.
```
pip install -r requirements.txt
```       
4. Setup table and migrations
```
python manage.py makemigrations
python manage.py migrate
```
5. Runser server
```
python manage.py runserver
```

### URLS
1. `loans/upload` : Upload and gather the file and save to database.
2. 'loans/lists/` : Retrived the list of loans based on user input (Simplify and Modify)

