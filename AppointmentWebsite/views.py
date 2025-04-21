from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import Http404
from .forms import TimeSlotForm, StudentFileForm, FileCommentForm
from .models import TimeSlot, Appointment, UserProfile, StudentFile, FileComment, Message, MessageReply
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
import os
from django.db.utils import IntegrityError
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count

def is_slot_expired(slot):
    """Check if a time slot is within 10 minutes of its end time"""
    now = timezone.now()
    slot_date = slot.date
    slot_end_time = slot.end_time
    
    # Combine date and time
    slot_end_datetime = datetime.combine(slot_date, slot_end_time)
    slot_end_datetime = timezone.make_aware(slot_end_datetime)
    
    # Check if current time is within 10 minutes of end time
    return now >= (slot_end_datetime - timedelta(minutes=10))

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
def view_file(request, file_id):
    student_file = get_object_or_404(StudentFile, id=file_id)
    
    # Check if user has permission to view the file
    user_profile = request.user.userprofile
    if user_profile.user_type != 'faculty' and student_file.student != request.user:
        raise PermissionDenied
    
    comments = FileComment.objects.filter(student_file=student_file)
    if user_profile.user_type != 'faculty':
        # Students can only see non-private comments
        comments = comments.filter(is_private=False)
    
    if request.method == 'POST' and user_profile.user_type == 'faculty':
        comment_form = FileCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.student_file = student_file
            comment.faculty = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
            return redirect('view_file', file_id=file_id)
    else:
        comment_form = FileCommentForm() if user_profile.user_type == 'faculty' else None
    
    return render(request, 'view_file.html', {
        'student_file': student_file,
        'comments': comments,
        'comment_form': comment_form,
        'is_faculty': user_profile.user_type == 'faculty'
    })

@login_required
def download_file(request, file_id):
    student_file = get_object_or_404(StudentFile, id=file_id)
    
    # Check if user has permission to download the file
    user_profile = request.user.userprofile
    if user_profile.user_type != 'faculty' and student_file.student != request.user:
        raise PermissionDenied
    
    file_path = student_file.file.path
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def book_appointment(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'faculty':
            return faculty_interface(request)
        
        # Student interface
        student_files = StudentFile.objects.filter(student=request.user).order_by('-uploaded_at')
        pending_files = student_files.filter(status='Pending')
        
        # Get all appointments for the current user
        appointments = {
            'all': Appointment.objects.filter(student=request.user).order_by('-time_slot__date', '-time_slot__start_time'),
            'pending': Appointment.objects.filter(student=request.user, status='Pending').order_by('-time_slot__date'),
            'approved': Appointment.objects.filter(student=request.user, status='Approved').order_by('-time_slot__date'),
            'completed': Appointment.objects.filter(student=request.user, status='Completed').order_by('-time_slot__date'),
            'cancelled': Appointment.objects.filter(student=request.user, status='Rejected').order_by('-time_slot__date')
        }
        
        if request.method == 'POST':
            if 'upload_file' in request.POST:
                file_form = StudentFileForm(request.POST, request.FILES)
                if file_form.is_valid():
                    student_file = file_form.save(commit=False)
                    student_file.student = request.user
                    student_file.save()
                    messages.success(request, 'File uploaded successfully!')
                    return redirect('book_appointment')
            elif 'book_slot' in request.POST:
                if not pending_files.exists():
                    messages.error(request, 'You must upload at least one file before booking an appointment.')
                    return redirect('book_appointment')
                
                time_slot_id = request.POST.get('time_slot')
                file_id = request.POST.get('student_file')
                
                try:
                    # Get the time slot and check if it's available
                    time_slot = TimeSlot.objects.get(id=time_slot_id)
                    
                    # Check if the slot is expired
                    if is_slot_expired(time_slot):
                        messages.error(request, 'This time slot has expired. Please select another time.')
                        return redirect('book_appointment')
                    
                    # Check if the time slot is already booked
                    if Appointment.objects.filter(time_slot=time_slot).exists():
                        messages.error(request, 'This time slot has already been booked. Please select another time.')
                        return redirect('book_appointment')
                    
                    # Get the student file
                    student_file = StudentFile.objects.get(id=file_id, student=request.user, status='Pending')
                    
                    # Create appointment
                    appointment = Appointment.objects.create(
                        student=request.user,
                        time_slot=time_slot,
                        status='Pending',
                        student_file=student_file
                    )
                    
                    # Update time slot availability
                    time_slot.is_available = False
                    time_slot.save()
                    
                    messages.success(request, 'Appointment booked successfully!')
                    return redirect('book_appointment')
                except TimeSlot.DoesNotExist:
                    messages.error(request, 'Selected time slot does not exist.')
                    return redirect('book_appointment')
                except StudentFile.DoesNotExist:
                    messages.error(request, 'Selected file does not exist or is not pending.')
                    return redirect('book_appointment')
                except Exception as e:
                    messages.error(request, 'An error occurred while booking the appointment. Please try again.')
                    return redirect('book_appointment')
        else:
            file_form = StudentFileForm()
        
        # Get all time slots
        all_slots = TimeSlot.objects.all().order_by('date', 'start_time')
        
        # Get current user's appointments
        user_appointments = appointments['all']
        booked_slot_ids = user_appointments.values_list('time_slot_id', flat=True)
        
        # Filter available and unavailable slots
        available_slots = []
        unavailable_slots = []
        
        for slot in all_slots:
            # Check if the slot is available, not booked, and not expired
            if (slot.is_available and 
                not Appointment.objects.filter(time_slot=slot).exists() and 
                not is_slot_expired(slot)):
                available_slots.append(slot)
            else:
                # Only show unavailable slots that belong to the current student
                if slot.id in booked_slot_ids:
                    try:
                        appointment = user_appointments.get(time_slot=slot)
                        slot.booking_status = appointment.status
                        slot.student_file = appointment.student_file
                        unavailable_slots.append(slot)
                    except Appointment.DoesNotExist:
                        continue
        
        return render(request, 'student_booking.html', {
            'available_slots': available_slots,
            'unavailable_slots': unavailable_slots,
            'file_form': file_form,
            'student_files': student_files,
            'pending_files': pending_files,
            'appointments': appointments
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
            
        # Get all appointments for this faculty
        appointments = {
            'all': Appointment.objects.filter(time_slot__faculty=request.user).order_by('-time_slot__date', '-time_slot__start_time'),
            'pending': Appointment.objects.filter(time_slot__faculty=request.user, status='Pending').order_by('-time_slot__date'),
            'approved': Appointment.objects.filter(time_slot__faculty=request.user, status='Approved').order_by('-time_slot__date'),
            'completed': Appointment.objects.filter(time_slot__faculty=request.user, status='Completed').order_by('-time_slot__date'),
            'cancelled': Appointment.objects.filter(time_slot__faculty=request.user, status='Rejected').order_by('-time_slot__date')
        }
            
        if request.method == 'POST':
            form = TimeSlotForm(request.POST)
            if form.is_valid():
                # Check for existing time slot with same date and time
                date = form.cleaned_data['date']
                start_time = form.cleaned_data['start_time']
                end_time = form.cleaned_data['end_time']
                room = form.cleaned_data['room']
                
                existing_slot = TimeSlot.objects.filter(
                    faculty=request.user,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    room=room
                ).exists()
                
                if existing_slot:
                    messages.error(request, 'A time slot with these details already exists.')
                    return redirect('book_appointment')
                
                time_slot = form.save(commit=False)
                time_slot.faculty = request.user
                time_slot.is_available = True
                time_slot.save()
                messages.success(request, 'Time slot added successfully!')
                return redirect('book_appointment')
        else:
            form = TimeSlotForm()
            # Get all time slots for this faculty
            existing_slots = TimeSlot.objects.filter(faculty=request.user).order_by('date', 'start_time')
            
            # Add appointment information to existing slots
            for slot in existing_slots:
                try:
                    appointment = appointments['all'].get(time_slot=slot)
                    slot.is_available = False
                    slot.student_name = appointment.student.get_full_name()
                    slot.student_file = appointment.student_file
                    slot.appointment = appointment
                    slot.appointment_status = appointment.status
                except Appointment.DoesNotExist:
                    # No appointment exists for this slot
                    slot.is_available = True
                    slot.student_name = None
                    slot.student_file = None
                    slot.appointment = None
                    slot.appointment_status = None
        
        return render(request, 'faculty_interface.html', {
            'form': form,
            'existing_slots': existing_slots,
            'appointments': appointments
        })
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')

@login_required
def approve_appointment(request, appointment_id):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            raise PermissionDenied
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        if appointment.time_slot.faculty != request.user:
            raise PermissionDenied
        
        # Update appointment status
        appointment.status = 'Approved'
        appointment.save()
        
        # Update file status
        if appointment.student_file:
            appointment.student_file.status = 'Approved'
            appointment.student_file.save()
        
        # Make the time slot appear available again
        time_slot = appointment.time_slot
        time_slot.is_available = True
        time_slot.save()
        
        messages.success(request, 'Appointment approved successfully!')
        return redirect('book_appointment')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')

@login_required
def reject_appointment(request, appointment_id):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            raise PermissionDenied
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        if appointment.time_slot.faculty != request.user:
            raise PermissionDenied
        
        # Update file status back to pending
        if appointment.student_file:
            appointment.student_file.status = 'Pending'
            appointment.student_file.save()
        
        # Make time slot available again
        time_slot = appointment.time_slot
        time_slot.is_available = True
        time_slot.save()
        
        # Mark appointment as rejected instead of deleting
        appointment.status = 'Rejected'
        appointment.save()
        
        messages.success(request, 'Appointment rejected successfully!')
        return redirect('book_appointment')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')

@login_required
def faculty_history(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            raise PermissionDenied("Only faculty members can access this page.")
        
        # Get all approved and rejected appointments for this faculty
        appointments = Appointment.objects.filter(
            time_slot__faculty=request.user
        ).exclude(
            status='Pending'
        ).order_by('-time_slot__date', '-time_slot__start_time')
        
        return render(request, 'faculty_history.html', {
            'appointments': appointments
        })
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get appointment statistics
    total_appointments = Appointment.objects.count()
    upcoming_appointments = Appointment.objects.filter(
        time_slot__date__gte=timezone.now().date(),
        status='Pending'
    ).count()
    completed_appointments = Appointment.objects.filter(status='Completed').count()
    cancelled_appointments = Appointment.objects.filter(status='Rejected').count()

    # Get appointment trends (last 7 days)
    today = timezone.now().date()
    last_week = today - timedelta(days=6)
    daily_appointments = (
        Appointment.objects.filter(time_slot__date__gte=last_week)
        .values('time_slot__date')
        .annotate(count=Count('id'))
        .order_by('time_slot__date')
    )

    # Get user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=30)).count()
    
    # Get recent users
    recent_users = User.objects.select_related('userprofile').order_by('-date_joined')[:10]

    context = {
        'total_appointments': total_appointments,
        'upcoming_appointments': upcoming_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'daily_appointments': list(daily_appointments),
        'total_users': total_users,
        'active_users': active_users,
        'recent_users': recent_users,
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
def messages_view(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type == 'student':
            # Get messages where the current user is either the student or receiving from faculty
            messages = Message.objects.filter(
                student=request.user
            ).order_by('-created_at')
            available_faculty = UserProfile.objects.filter(user_type='faculty')
        else:
            # For faculty, show messages where they are the faculty member
            messages = Message.objects.filter(
                faculty=request.user
            ).order_by('-created_at')
            available_faculty = None

        return render(request, 'messages.html', {
            'messages': messages,
            'available_faculty': available_faculty
        })
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')

@login_required
def send_message(request):
    if request.method == 'POST':
        try:
            user_profile = request.user.userprofile
            content = request.POST.get('content')
            
            if not content:
                return JsonResponse({'success': False, 'error': 'Message content is required'})

            if user_profile.user_type == 'student':
                # Student sending message to faculty
                recipient_id = request.POST.get('recipient_id')
                if not recipient_id:
                    return JsonResponse({'success': False, 'error': 'Recipient is required'})

                try:
                    faculty = User.objects.get(id=recipient_id)
                    faculty_profile = faculty.userprofile
                    if faculty_profile.user_type != 'faculty':
                        return JsonResponse({'success': False, 'error': 'Invalid recipient'})

                    message = Message.objects.create(
                        student=request.user,
                        faculty=faculty,
                        content=content,
                        sender_type='student',
                        attachment=request.FILES.get('attachment')
                    )
                    return JsonResponse({
                        'success': True,
                        'message': {
                            'content': message.content,
                            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'sender_type': 'student'
                        }
                    })
                except User.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Faculty not found'})
            else:
                # Faculty sending message to student
                student_id = request.POST.get('recipient_id')
                if not student_id:
                    return JsonResponse({'success': False, 'error': 'Recipient is required'})

                try:
                    student = User.objects.get(id=student_id)
                    student_profile = student.userprofile
                    if student_profile.user_type != 'student':
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
                            'content': message.content,
                            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'sender_type': 'faculty'
                        }
                    })
                except User.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Student not found'})

        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User profile not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def faculty_messages_view(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.user_type != 'faculty':
            raise PermissionDenied
        
        # Get selected student_id from query parameters
        selected_student_id = request.GET.get('student_id')
        
        if selected_student_id:
            # Get messages only for the selected student
            messages = Message.objects.filter(
                faculty=request.user,
                student_id=selected_student_id
            ).order_by('-created_at')
        else:
            # If no student selected, get all messages to show in the sidebar
            messages = Message.objects.filter(
                faculty=request.user
            ).order_by('-created_at')

        # Get unique students who have messaged this faculty
        students = User.objects.filter(
            userprofile__user_type='student',
            student_messages__faculty=request.user
        ).distinct()

        return render(request, 'faculty_messages.html', {
            'messages': messages,
            'students': students  # Pass the students list separately
        })
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found')
        return redirect('logout')
