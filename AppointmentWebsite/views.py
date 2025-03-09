from django.shortcuts import render, redirect
from .forms import AppointmentForm

def homepage(request):
    return render(request, 'home.html')

def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()  # Save the appointment to the database
            return redirect('home')  # Redirect to homepage after booking
        else:
            print(form.errors)  # Print errors to console for debugging
    else:
        form = AppointmentForm()  # Create a new form instance for GET requests

    # Always return the form, whether it's valid or not
    return render(request, 'book_appointment.html', {'form': form})
