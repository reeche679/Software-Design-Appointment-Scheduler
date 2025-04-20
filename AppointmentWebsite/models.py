from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=[('student', 'Student'), ('faculty', 'Faculty')])
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    # Faculty-specific fields
    title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    office_location = models.CharField(max_length=100, blank=True, null=True)
    office_hours = models.CharField(max_length=200, blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    research_interests = models.TextField(blank=True, null=True)
    years_of_experience = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class StudentFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('THESIS', 'Thesis Document'),
        ('PROPOSAL', 'Research Proposal'),
        ('DOCUMENTATION', 'Project Documentation'),
        ('OTHER', 'Other Documents')
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file = models.FileField(upload_to='student_files/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"{self.student.username} - {self.get_file_type_display()} - {self.uploaded_at.date()}"

class FileComment(models.Model):
    student_file = models.ForeignKey(StudentFile, on_delete=models.CASCADE, related_name='comments')
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_comments')
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_private = models.BooleanField(default=False, help_text="If checked, only faculty can see this comment")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.faculty.username} on {self.student_file}"

class TimeSlot(models.Model):
    ROOM_CHOICES = [
        ('CICS201', 'CICS 201'),
        ('CICS202', 'CICS 202'),
        ('CPE_FACULTY', 'CpE FACULTY'),
        ('COMP_LAB_CICS', 'COMPUTER ENGINEERING LAB (CICS)'),
        ('COMP_LAB_EINSTEIN', 'COMPUTER LAB (EINSTEIN BUILDING)'),
        ('ICT_FACULTY', 'ICT FACULTY (GYM)')
    ]

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, choices=ROOM_CHOICES, default='CICS201')
    is_available = models.BooleanField(default=True)
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_slots')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.faculty.username} - {self.get_room_display()} - {self.date} ({self.start_time} - {self.end_time})"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ]

    REASON_CHOICES = [
        ('consultation', 'Consultation'),
        ('thesis', 'Thesis Defense'),
        ('proposal', 'Proposal Defense'),
        ('other', 'Other')
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    time_slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    student_file = models.ForeignKey(StudentFile, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.time_slot}"

class Message(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.student.get_full_name()} to {self.faculty.get_full_name()}"

class MessageReply(models.Model):
    SENDER_TYPES = (
        ('student', 'Student'),
        ('faculty', 'Faculty'),
    )

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='replies')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Message replies'

    def __str__(self):
        return f"Reply to message {self.message.id} by {self.sender.get_full_name()}"