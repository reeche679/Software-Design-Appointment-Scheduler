from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import TimeSlotForm
from .models import TimeSlot, Appointment, UserProfile
from django.contrib import messages
from django.core.exceptions import PermissionDenied

@login_required
def homepage(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'student':
            return redirect('book_appointment')
        else:
            return redirect('book_appointment')  # This will show faculty interface due to user_type check
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')

@login_required
def book_appointment(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'faculty':
            return faculty_interface(request)
        
        # Student interface
        if request.method == 'POST':
            time_slot_id = request.POST.get('time_slot')
            
            try:
                time_slot = TimeSlot.objects.get(id=time_slot_id, is_available=True)
                appointment = Appointment.objects.create(
                    student=request.user,
                    time_slot=time_slot,
                    status='Scheduled'
                )
                time_slot.is_available = False
                time_slot.save()
                messages.success(request, 'Appointment booked successfully!')
                return redirect('book_appointment')
            except TimeSlot.DoesNotExist:
                messages.error(request, 'Sorry, this time slot is no longer available.')
        
        # Get available time slots
        available_slots = TimeSlot.objects.filter(is_available=True).order_by('date', 'start_time')
        return render(request, 'student_booking.html', {
            'available_slots': available_slots
        })
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')

@login_required
def faculty_interface(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            raise PermissionDenied
            
        if request.method == 'POST':
            form = TimeSlotForm(request.POST)
            if form.is_valid():
                time_slot = form.save(commit=False)
                time_slot.faculty = request.user
                time_slot.is_available = True
                time_slot.save()
                messages.success(request, 'Time slot added successfully!')
                return redirect('book_appointment')
        else:
            form = TimeSlotForm()
            existing_slots = TimeSlot.objects.filter(faculty=request.user)
        
        return render(request, 'faculty_interface.html', {
            'form': form,
            'existing_slots': existing_slots
        })
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')
