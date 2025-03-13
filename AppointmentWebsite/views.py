from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import AppointmentForm, TimeSlotForm
from .models import TimeSlot, Appointment
from django.contrib import messages

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def homepage(request):
    user_types = {
        'student': 'Student',
        'faculty': 'Faculty'
    }
    return render(request, 'home.html', {'user_types': user_types})

@login_required
def book_appointment(request):
    user_type = request.GET.get('user_type', 'student')
    
    if user_type == 'faculty':
        return faculty_interface(request)
    
    # Student interface
    if request.method == 'POST':
        time_slot_id = request.POST.get('time_slot')
        client_name = request.POST.get('client_name')
        
        try:
            time_slot = TimeSlot.objects.get(id=time_slot_id, is_available=True)
            appointment = Appointment.objects.create(
                client_name=client_name,
                appointment_date=f"{time_slot.date} {time_slot.start_time}",
                service=f"Meeting with {time_slot.faculty}",
                status='Scheduled'
            )
            time_slot.is_available = False
            time_slot.save()
            messages.success(request, 'Appointment booked successfully!')
            return redirect('home')
        except TimeSlot.DoesNotExist:
            messages.error(request, 'Sorry, this time slot is no longer available.')
    
    # Get available time slots
    available_slots = TimeSlot.objects.filter(is_available=True).order_by('date', 'start_time')
    return render(request, 'student_booking.html', {
        'available_slots': available_slots
    })

@login_required
def faculty_interface(request):
    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            time_slot = form.save(commit=False)
            time_slot.is_available = True
            time_slot.save()
            messages.success(request, 'Time slot added successfully!')
            return redirect('book_appointment')
    else:
        form = TimeSlotForm()
        existing_slots = TimeSlot.objects.all()
    
    return render(request, 'faculty_interface.html', {
        'form': form,
        'existing_slots': existing_slots
    })