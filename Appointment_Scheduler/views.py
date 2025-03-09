from django.http import*
from django.shortcuts import*


def homepage(request):
    return render(request,'home.html')

def Book_Appointment(request):
    return render(request,'book_appointment.html')