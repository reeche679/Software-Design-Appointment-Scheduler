from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from AppointmentWebsite.models import Appointment, UserProfile, TimeSlot, Message, MessageReply, User  # Updated import
from django.contrib import messages
from .forms import UserProfileForm  # We'll create this form next
from django.utils import timezone
import json
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from datetime import datetime

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

    today = timezone.now().date()
    
    # Get pending appointments count
    pending_appointments_count = Appointment.objects.filter(
        time_slot__faculty=request.user,
        status='Pending'
    ).count()

    # Get today's appointments
    todays_appointments = Appointment.objects.filter(
        time_slot__faculty=request.user,
        time_slot__date=today,
        status='Approved'
    ).select_related('student', 'time_slot').order_by('time_slot__start_time')
    
    todays_appointments_count = todays_appointments.count()

    # Get this week's appointments (next 7 days)
    week_end = today + timezone.timedelta(days=7)
    weekly_appointments_count = Appointment.objects.filter(
        time_slot__faculty=request.user,
        time_slot__date__range=[today, week_end],
        status='Approved'
    ).count()

    # Get unread messages count
    unread_messages_count = Message.objects.filter(
        faculty=request.user,
        is_read=False
    ).count()

    # Get upcoming appointments for display
    upcoming_appointments = Appointment.objects.filter(
        time_slot__faculty=request.user,
        time_slot__date__gte=today
    ).select_related('student', 'time_slot').order_by('time_slot__date', 'time_slot__start_time')

    # Get time slots
    time_slots = TimeSlot.objects.filter(
        faculty=request.user,
        date__gte=today
    ).order_by('date', 'start_time')

    # Get pending appointments for the tab
    pending_appointments = Appointment.objects.filter(
        time_slot__faculty=request.user,
        status='Pending'
    ).select_related('student', 'time_slot').order_by('time_slot__date', 'time_slot__start_time')

    context = {
        'pending_appointments_count': pending_appointments_count,
        'todays_appointments_count': todays_appointments_count,
        'weekly_appointments_count': weekly_appointments_count,
        'unread_messages_count': unread_messages_count,
        'todays_appointments': todays_appointments,
        'upcoming_appointments': upcoming_appointments,
        'time_slots': time_slots,
        'pending_appointments': pending_appointments,  # Pass the queryset directly
        'today': today,
    }
    return render(request, 'faculty_dashboard.html', context)

@login_required
def add_time_slot(request):
    if request.method == 'POST':
        try:
            # Verify user is faculty
            if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'faculty':
                raise PermissionDenied("Only faculty members can add time slots")

            # Get form data and parse date/time
            date_str = request.POST.get('date')
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            room = request.POST.get('room')

            # Parse the date and time strings
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()

            # Create new time slot
            time_slot = TimeSlot.objects.create(
                faculty=request.user,
                date=date,
                start_time=start_time,
                end_time=end_time,
                room=room,
                is_available=True
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'slot': {
                        'id': time_slot.id,
                        'date': date_str,  # Use the original string format for the response
                        'start_time': start_time_str,  # Use the original string format
                        'end_time': end_time_str,  # Use the original string format
                        'room': room
                    }
                })

            messages.success(request, 'Time slot added successfully!')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
            messages.error(request, str(e))

    return redirect('faculty_schedule')

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

    # Get faculty's time slots with related appointment information
    time_slots = TimeSlot.objects.filter(
        faculty=request.user
    ).select_related(
        'appointment'  # Use select_related since it's a OneToOneField
    ).order_by('date', 'start_time')

    # Annotate each time slot with appointment information
    for slot in time_slots:
        try:
            # Since it's a OneToOneField, we can access it directly
            slot.is_booked = hasattr(slot, 'appointment')
            if slot.is_booked:
                slot.appointment = slot.appointment
            else:
                slot.appointment = None
        except Exception:
            slot.appointment = None
            slot.is_booked = False

    # Create a list of open slots (not booked)
    open_slots = [slot for slot in time_slots if not slot.is_booked]

    context = {
        'time_slots': time_slots,
        'open_slots': open_slots,
        'today': timezone.now().date(),
    }
    return render(request, 'faculty_schedule.html', context)

@login_required
def delete_time_slot(request, slot_id):
    try:
        time_slot = TimeSlot.objects.get(id=slot_id, faculty=request.user)
        
        # Check if the time slot has an appointment
        if hasattr(time_slot, 'appointment'):
            raise ValueError("Cannot delete a time slot that has an appointment.")
            
        time_slot.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Time slot deleted successfully'
            })
            
        messages.success(request, "Time slot deleted successfully.")
        
    except TimeSlot.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'Time slot not found'
            }, status=404)
        messages.error(request, "Time slot not found.")
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        messages.error(request, str(e))
    
    return redirect('faculty_schedule')

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
def faculty_messages_view(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            raise PermissionDenied
        
        # Get selected student_id from query parameters
        selected_student_id = request.GET.get('student_id')
        
        # Get all students who have messages with this faculty
        students = User.objects.filter(
            student_messages__faculty=request.user  # Get students who have messages with this faculty
        ).distinct()  # Use distinct to avoid duplicates

        if selected_student_id:
            # Get messages only for the selected student
            messages = Message.objects.filter(
                faculty=request.user,
                student_id=selected_student_id
            ).order_by('-created_at')
        else:
            # If no student selected, get all messages
            messages = Message.objects.filter(
                faculty=request.user
            ).order_by('-created_at')

        print(f"Number of students found: {students.count()}")  # Debug print
        print(f"Students: {[s.get_full_name() for s in students]}")  # Debug print
        print(f"Number of messages: {messages.count()}")  # Debug print

        return render(request, 'faculty_messages.html', {
            'messages': messages,
            'students': students
        })
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')

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
    if request.method == 'POST':
        try:
            user_profile = request.user.userprofile
            content = request.POST.get('content')
            recipient_id = request.POST.get('recipient_id')

            if not content or not recipient_id:
                return JsonResponse({'success': False, 'error': 'Missing required fields'})

            try:
                if user_profile.user_type == 'student':
                    # Student sending to faculty
                    faculty = User.objects.get(id=recipient_id)
                    if faculty.userprofile.user_type != 'faculty':
                        return JsonResponse({'success': False, 'error': 'Invalid recipient'})
                    
                    message = Message.objects.create(
                        student=request.user,
                        faculty=faculty,
                        content=content,
                        sender_type='student',
                        attachment=request.FILES.get('attachment')
                    )
                else:
                    # Faculty sending to student
                    student = User.objects.get(id=recipient_id)
                    if student.userprofile.user_type != 'student':
                        return JsonResponse({'success': False, 'error': 'Invalid recipient'})
                    
                    message = Message.objects.create(
                        student=student,
                        faculty=request.user,
                        content=content,
                        sender_type='faculty',
                        attachment=request.FILES.get('attachment')
                    )

                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'content': content,
                        'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'sender_type': message.sender_type
                    }
                })
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Recipient not found'})

        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User profile not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@require_POST
def approve_appointment(request, appointment_id):
    try:
        # Get the appointment and verify the faculty member is authorized
        appointment = get_object_or_404(Appointment, id=appointment_id)
        if appointment.time_slot.faculty != request.user:
            messages.error(request, "You are not authorized to approve this appointment.")
            return redirect('faculty_dashboard')
        
        # Update appointment status
        appointment.status = 'Approved'
        appointment.save()
        
        # Update file status if there's an associated file
        if appointment.student_file:
            appointment.student_file.status = 'Approved'
            appointment.student_file.save()
        
        messages.success(request, f"Appointment with {appointment.student.get_full_name()} has been approved.")
    except Exception as e:
        messages.error(request, f"Error approving appointment: {str(e)}")
    
    return redirect('faculty_dashboard')

@login_required
@require_POST
def reject_appointment(request, appointment_id):
    try:
        # Get the appointment and verify the faculty member is authorized
        appointment = get_object_or_404(Appointment, id=appointment_id)
        if appointment.time_slot.faculty != request.user:
            messages.error(request, "You are not authorized to reject this appointment.")
            return redirect('faculty_dashboard')
        
        # Update appointment status
        appointment.status = 'Rejected'
        appointment.save()
        
        # Update file status if there's an associated file
        if appointment.student_file:
            appointment.student_file.status = 'Pending'
            appointment.student_file.save()
        
        # Make the time slot available again
        appointment.time_slot.is_available = True
        appointment.time_slot.save()
        
        messages.success(request, f"Appointment with {appointment.student.get_full_name()} has been rejected.")
    except Exception as e:
        messages.error(request, f"Error rejecting appointment: {str(e)}")
    
    return redirect('faculty_dashboard')