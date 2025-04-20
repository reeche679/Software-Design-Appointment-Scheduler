from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from AppointmentWebsite.models import Appointment, UserProfile, TimeSlot, Message, MessageReply, User  # Updated import
from django.contrib import messages
from .forms import UserProfileForm  # We'll create this form next
from django.utils import timezone
import json
from django.views.decorators.http import require_POST

@login_required
def homepage(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'faculty':
            return redirect('faculty_dashboard')
        else:
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        return redirect('edit_profile')

@login_required
def Book_Appointment(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'faculty':
            messages.error(request, "Faculty members cannot book appointments.")
            return redirect('faculty_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('edit_profile')

    # Get the selected date from query parameters, default to today
    selected_date = request.GET.get('date', timezone.now().date())
    if isinstance(selected_date, str):
        selected_date = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()

    # Get available time slots for the selected date
    available_slots = TimeSlot.objects.filter(
        date=selected_date,
        is_available=True
    ).select_related('faculty', 'faculty__userprofile').order_by('start_time')

    # Group time slots by faculty
    faculty_slots = {}
    for slot in available_slots:
        if slot.faculty not in faculty_slots:
            faculty_slots[slot.faculty] = []
        faculty_slots[slot.faculty].append(slot)

    # Get all appointments for the current user with related data
    try:
        print(f"\nDebug: Fetching appointments for user {request.user.username}")
        print(f"Debug: User ID: {request.user.id}")
        
        all_appointments = Appointment.objects.filter(
            student=request.user
        ).select_related(
            'time_slot',
            'time_slot__faculty'
        ).prefetch_related(
            'time_slot__faculty__userprofile'
        ).order_by('-time_slot__date', '-time_slot__start_time')

        print(f"Debug: Raw SQL query: {all_appointments.query}")
        print(f"Debug: Total appointments found: {all_appointments.count()}")
        
        # Categorize appointments by status
        appointments = {
            'all': all_appointments,
            'pending': all_appointments.filter(status='Pending'),
            'approved': all_appointments.filter(status='Approved'),
            'rejected': all_appointments.filter(status='Rejected')
        }

        # Print status counts and details
        for status, appts in appointments.items():
            print(f"\nDebug: {status.capitalize()} appointments: {appts.count()}")
            for appt in appts:
                print(f"  - ID: {appt.id}")
                print(f"  - Date: {appt.time_slot.date}")
                print(f"  - Faculty: {appt.time_slot.faculty.get_full_name()}")
                print(f"  - Status: {appt.status}")

    except Exception as e:
        print(f"Debug: Error fetching appointments: {str(e)}")
        print(f"Debug: Exception type: {type(e)}")
        appointments = {
            'all': [],
            'pending': [],
            'approved': [],
            'rejected': []
        }

    context = {
        'selected_date': selected_date,
        'faculty_slots': faculty_slots,
        'today': timezone.now().date(),
        'appointments': appointments,
        'user': request.user,
        'debug_info': {
            'username': request.user.username,
            'total_appointments': len(appointments['all']),
            'status_counts': {status: len(appts) for status, appts in appointments.items()}
        }
    }
    return render(request, 'Book_Appointment.html', context)

@login_required
def dashboard(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'faculty':
            return redirect('faculty_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('edit_profile')

    # Get user's upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        student=request.user,
        time_slot__date__gte=timezone.now().date()
    ).select_related('time_slot', 'time_slot__faculty').order_by('time_slot__date', 'time_slot__start_time')[:5]

    # Get available faculty members
    available_faculty = UserProfile.objects.filter(
        user_type='faculty'
    ).select_related('user')

    # Get recent messages
    recent_messages = Message.objects.filter(
        student=request.user
    ).order_by('-created_at')[:5]

    context = {
        'upcoming_appointments': upcoming_appointments,
        'available_faculty': available_faculty,
        'recent_messages': recent_messages,
    }
    return render(request, 'registration/dashboard.html', context)

@login_required
def profile(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'faculty':
            return redirect('faculty_profile')
    except UserProfile.DoesNotExist:
        return redirect('edit_profile')

    # Get the user's appointments
    appointments = Appointment.objects.filter(student=request.user).order_by('-created_at')
    
    context = {
        'user_profile': user_profile,
        'appointments': appointments
    }
    return render(request, 'profile.html', context)

@login_required
def edit_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile(user=request.user)
    
    if request.method == 'POST':
        # Update user's first and last name
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        
        # Update phone number in user profile
        user_profile.phone_number = request.POST.get('phone_number', '')
        user_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'edit_profile.html', {
        'user_profile': user_profile,
        'user': request.user
    })

@login_required
def schedule(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'faculty':
            return redirect('faculty_schedule')
    except UserProfile.DoesNotExist:
        return redirect('edit_profile')

    # Get student's appointments
    appointments = Appointment.objects.filter(student=request.user).select_related(
        'time_slot', 'time_slot__faculty'
    ).order_by('time_slot__date', 'time_slot__start_time')

    # Create a set of dates that have appointments
    appointment_dates = set(appointment.time_slot.date for appointment in appointments)
    
    context = {
        'appointment_dates': appointment_dates,
        'today': timezone.now().date(),
    }
    return render(request, 'schedule.html', context)

@login_required
def messages_view(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'faculty':
            return redirect('faculty_messages')
    except UserProfile.DoesNotExist:
        return redirect('edit_profile')

    faculty_id = request.GET.get('faculty_id')
    
    # Get student's messages
    messages_query = Message.objects.filter(student=request.user)
    if faculty_id:
        messages_query = messages_query.filter(faculty_id=faculty_id)
    
    student_messages = messages_query.prefetch_related('replies').order_by('-created_at')
    
    # Get available faculty members
    available_faculty = UserProfile.objects.filter(
        user_type='faculty'
    ).select_related('user')
    
    context = {
        'messages': student_messages,
        'unread_count': student_messages.filter(is_read=False).count(),
        'available_faculty': available_faculty,
        'selected_faculty_id': faculty_id
    }
    return render(request, 'messages.html', context)

@login_required
def faculty_dashboard(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            messages.error(request, "You don't have permission to access the faculty dashboard.")
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile to access the faculty dashboard.")
        return redirect('edit_profile')

    # Get faculty's upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        time_slot__faculty=request.user,
        time_slot__date__gte=timezone.now().date()
    ).select_related('student', 'time_slot').order_by('time_slot__date', 'time_slot__start_time')

    # Get faculty's time slots
    time_slots = TimeSlot.objects.filter(
        faculty=request.user,
        date__gte=timezone.now().date()
    ).order_by('date', 'start_time')

    # Get faculty's messages
    faculty_messages = Message.objects.filter(
        faculty=request.user
    ).prefetch_related('replies').order_by('-created_at')
    
    context = {
        'upcoming_appointments': upcoming_appointments,
        'time_slots': time_slots,
        'messages': faculty_messages,
        'today': timezone.now().date(),
    }
    return render(request, 'faculty_dashboard.html', context)

@login_required
def add_time_slot(request):
    if request.method == 'POST':
        try:
            date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            room = request.POST.get('room')

            # Create new time slot
            TimeSlot.objects.create(
                faculty=request.user,
                date=date,
                start_time=start_time,
                end_time=end_time,
                room=room,
                is_available=True
            )
            messages.success(request, 'Time slot added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding time slot: {str(e)}')
        
        return redirect('faculty_dashboard')
    
    return redirect('faculty_dashboard')

@login_required
def suggest_alternative(request):
    if request.method == 'POST':
        try:
            appointment_id = request.POST.get('appointment_id')
            suggested_date = request.POST.get('suggested_date')
            suggested_start_time = request.POST.get('suggested_start_time')
            suggested_end_time = request.POST.get('suggested_end_time')
            suggested_room = request.POST.get('suggested_room')

            # Get the original appointment
            appointment = Appointment.objects.get(id=appointment_id)
            
            # Create a new time slot for the suggestion
            suggested_slot = TimeSlot.objects.create(
                faculty=request.user,
                date=suggested_date,
                start_time=suggested_start_time,
                end_time=suggested_end_time,
                room=suggested_room,
                is_available=True
            )

            # Update the appointment with the suggested time slot
            appointment.suggested_time_slot = suggested_slot
            appointment.status = 'suggested'
            appointment.save()

            messages.success(request, 'Alternative time suggested successfully!')
        except Exception as e:
            messages.error(request, f'Error suggesting alternative time: {str(e)}')
        
        return redirect('faculty_dashboard')
    
    return redirect('faculty_dashboard')

@login_required
def faculty_schedule(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            messages.error(request, "You don't have permission to access the faculty schedule.")
            return redirect('schedule')
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile to access the faculty schedule.")
        return redirect('edit_profile')

    # Get faculty's time slots
    time_slots = TimeSlot.objects.filter(
        faculty=request.user
    ).order_by('date', 'start_time')

    context = {
        'time_slots': time_slots,
        'today': timezone.now().date(),
    }
    return render(request, 'faculty_schedule.html', context)

@login_required
def delete_time_slot(request, slot_id):
    try:
        # Get the time slot
        time_slot = TimeSlot.objects.get(id=slot_id, faculty=request.user)
        
        # Check if the slot is already booked
        if time_slot.is_booked:
            messages.error(request, "Cannot delete a booked time slot.")
            return redirect('faculty_dashboard')
            
        # Delete the time slot
        time_slot.delete()
        messages.success(request, "Time slot deleted successfully.")
    except TimeSlot.DoesNotExist:
        messages.error(request, "Time slot not found.")
    except Exception as e:
        messages.error(request, f"Error deleting time slot: {str(e)}")
    
    return redirect('faculty_dashboard')

@login_required
@require_POST
def mark_message_as_read(request, message_id):
    try:
        message = Message.objects.get(id=message_id, faculty=request.user)
        message.is_read = True
        message.save()
        return JsonResponse({'status': 'success'})
    except Message.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Message not found'}, status=404)

@login_required
@require_POST
def reply_to_message(request, message_id):
    try:
        data = json.loads(request.body)
        user_profile = request.user.userprofile
        
        # Allow both students and faculty to reply
        if user_profile.user_type == 'faculty':
            message = Message.objects.get(id=message_id, faculty=request.user)
        else:
            message = Message.objects.get(id=message_id, student=request.user)
        
        reply = MessageReply.objects.create(
            message=message,
            sender=request.user,
            sender_type=user_profile.user_type,
            content=data['content']
        )
        
        # Mark the original message as read when replying
        message.is_read = True
        message.save()
        
        return JsonResponse({
            'status': 'success',
            'sender_name': request.user.get_full_name(),
            'content': reply.content,
            'created_at': reply.created_at.isoformat()
        })
    except Message.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Message not found'}, status=404)
    except KeyError:
        return JsonResponse({'status': 'error', 'message': 'Missing content'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

@login_required
def faculty_messages(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            messages.error(request, "You don't have permission to access faculty messages.")
            return redirect('messages')
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile to access faculty messages.")
        return redirect('edit_profile')

    # Get faculty's messages
    faculty_messages = Message.objects.filter(
        faculty=request.user
    ).prefetch_related('replies').order_by('-created_at')
    
    # Get available students
    available_students = UserProfile.objects.filter(
        user_type='student'
    ).select_related('user')
    
    context = {
        'messages': faculty_messages,
        'unread_count': faculty_messages.filter(is_read=False).count(),
        'available_students': available_students
    }
    return render(request, 'faculty_messages.html', context)

@login_required
def faculty_profile(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            messages.error(request, "You don't have permission to access the faculty profile.")
            return redirect('profile')
    except UserProfile.DoesNotExist:
        messages.error(request, "Please complete your profile to access the faculty profile.")
        return redirect('edit_profile')
    
    context = {
        'user_profile': user_profile,
    }
    return render(request, 'faculty_profile.html', context)

@login_required
def confirm_appointment(request):
    if request.method == 'POST':
        try:
            time_slot_id = request.POST.get('time_slot_id')
            reason = request.POST.get('reason')
            
            print(f"Received appointment request:")
            print(f"Time slot ID: {time_slot_id}")
            print(f"Reason: {reason}")
            print(f"User: {request.user.username}")
            
            # Get the time slot
            time_slot = TimeSlot.objects.get(id=time_slot_id)
            print(f"Found time slot with faculty: {time_slot.faculty.username}")
            
            # Create the appointment
            appointment = Appointment.objects.create(
                student=request.user,
                time_slot=time_slot,
                reason=reason,
                status='Pending'
            )
            print(f"Created appointment with ID: {appointment.id}")
            
            # Update time slot availability
            time_slot.is_available = False
            time_slot.save()
            print(f"Updated time slot availability")
            
            messages.success(request, 'Appointment booked successfully! It is now pending approval.')
            return redirect('book_appointment')
            
        except TimeSlot.DoesNotExist:
            print(f"Error: Time slot {time_slot_id} not found")
            messages.error(request, 'Selected time slot does not exist.')
            return redirect('book_appointment')
        except Exception as e:
            print(f"Error creating appointment: {str(e)}")
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('book_appointment')
    else:
        print("Received non-POST request to confirm_appointment")
    
    return redirect('book_appointment')

@login_required
@require_POST
def send_message(request):
    try:
        user_profile = request.user.userprofile
        recipient_id = request.POST.get('recipient_id')  # Changed from faculty_id
        content = request.POST.get('content')
        attachment = request.FILES.get('attachment')

        if not recipient_id or not content:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

        recipient = User.objects.get(id=recipient_id)
        recipient_profile = recipient.userprofile

        # Check if the sender and recipient have valid roles
        if user_profile.user_type == 'faculty' and recipient_profile.user_type != 'student':
            return JsonResponse({'status': 'error', 'message': 'Can only send messages to students'}, status=400)
        elif user_profile.user_type == 'student' and recipient_profile.user_type != 'faculty':
            return JsonResponse({'status': 'error', 'message': 'Can only send messages to faculty'}, status=400)

        # Create message based on sender type
        if user_profile.user_type == 'faculty':
            message = Message.objects.create(
                student=recipient,
                faculty=request.user,
                content=content,
                attachment=attachment
            )
        else:
            message = Message.objects.create(
                student=request.user,
                faculty=recipient,
                content=content,
                attachment=attachment
            )

        return JsonResponse({
            'status': 'success',
            'message_id': message.id,
            'recipient_name': recipient.get_full_name(),
            'content': message.content,
            'created_at': message.created_at.isoformat()
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Recipient not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def approve_appointment(request, appointment_id):
    if request.method == 'POST':
        try:
            # Get the appointment and verify the faculty member is authorized
            appointment = get_object_or_404(Appointment, id=appointment_id)
            if appointment.time_slot.faculty != request.user:
                messages.error(request, "You are not authorized to approve this appointment.")
                return redirect('faculty_dashboard')
            
            # Update appointment status
            appointment.status = 'Approved'
            appointment.save()
            
            messages.success(request, f"Appointment with {appointment.student.get_full_name()} has been approved.")
        except Exception as e:
            messages.error(request, f"Error approving appointment: {str(e)}")
    
    return redirect('faculty_dashboard')

@login_required
def reject_appointment(request, appointment_id):
    if request.method == 'POST':
        try:
            # Get the appointment and verify the faculty member is authorized
            appointment = get_object_or_404(Appointment, id=appointment_id)
            if appointment.time_slot.faculty != request.user:
                messages.error(request, "You are not authorized to reject this appointment.")
                return redirect('faculty_dashboard')
            
            # Update appointment status
            appointment.status = 'Rejected'
            appointment.save()
            
            # Make the time slot available again
            appointment.time_slot.is_available = True
            appointment.time_slot.save()
            
            messages.success(request, f"Appointment with {appointment.student.get_full_name()} has been rejected.")
        except Exception as e:
            messages.error(request, f"Error rejecting appointment: {str(e)}")
    
    return redirect('faculty_dashboard')