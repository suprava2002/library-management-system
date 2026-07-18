from django.db import models
from django.utils import timezone
from datetime import timedelta


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=100, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    added_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.available_copies > 0


class Student(models.Model):
    name = models.CharField(max_length=150)
    roll_number = models.CharField(max_length=30, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    joined_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.roll_number})"


class IssueRecord(models.Model):
    STATUS_CHOICES = [
        ('ISSUED', 'Issued'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issue_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='issue_records')
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    return_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ISSUED')

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = timezone.now().date() + timedelta(days=14)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.status == 'ISSUED' and self.due_date and timezone.now().date() > self.due_date:
            return True
        return False

    def __str__(self):
        return f"{self.book.title} -> {self.student.name} ({self.status})"
