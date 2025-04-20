# Create and activate virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Green
python -m venv venv
Write-Host "Activating virtual environment..." -ForegroundColor Green
.\venv\Scripts\activate

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Green
pip install -r requirements.txt

# Make and apply migrations
Write-Host "Setting up database..." -ForegroundColor Green
python manage.py makemigrations
python manage.py migrate

# Create superuser
Write-Host "Creating superuser..." -ForegroundColor Green
python manage.py createsuperuser

# Run server
Write-Host "Starting development server..." -ForegroundColor Green
python manage.py runserver 