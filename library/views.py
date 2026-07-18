from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Book, Student, IssueRecord


def dashboard(request):
    total_books = Book.objects.count()
    total_students = Student.objects.count()
    books_issued = IssueRecord.objects.filter(status='ISSUED').count()
    overdue = [r for r in IssueRecord.objects.filter(status='ISSUED') if r.is_overdue]

    context = {
        'total_books': total_books,
        'total_students': total_students,
        'books_issued': books_issued,
        'overdue_count': len(overdue),
        'recent_issues': IssueRecord.objects.order_by('-issue_date')[:5],
    }
    return render(request, 'library/dashboard.html', context)


def book_list(request):
    query = request.GET.get('q', '')
    books = Book.objects.all()
    if query:
        books = books.filter(
            Q(title__icontains=query) | Q(author__icontains=query) | Q(isbn__icontains=query)
        )
    return render(request, 'library/book_list.html', {'books': books, 'query': query})


def book_add(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        category = request.POST.get('category')
        total_copies = int(request.POST.get('total_copies', 1))

        Book.objects.create(
            title=title, author=author, isbn=isbn, category=category,
            total_copies=total_copies, available_copies=total_copies
        )
        messages.success(request, f'Book "{title}" added successfully.')
        return redirect('book_list')
    return render(request, 'library/book_form.html')


def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    messages.success(request, 'Book deleted.')
    return redirect('book_list')


def student_list(request):
    query = request.GET.get('q', '')
    students = Student.objects.all()
    if query:
        students = students.filter(Q(name__icontains=query) | Q(roll_number__icontains=query))
    return render(request, 'library/student_list.html', {'students': students, 'query': query})


def student_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        roll_number = request.POST.get('roll_number')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        Student.objects.create(name=name, roll_number=roll_number, email=email, phone=phone)
        messages.success(request, f'Student "{name}" added successfully.')
        return redirect('student_list')
    return render(request, 'library/student_form.html')


def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.delete()
    messages.success(request, 'Student deleted.')
    return redirect('student_list')


def issue_list(request):
    status_filter = request.GET.get('status', '')
    records = IssueRecord.objects.select_related('book', 'student').order_by('-issue_date')
    if status_filter:
        records = records.filter(status=status_filter)
    return render(request, 'library/issue_list.html', {'records': records, 'status_filter': status_filter})


def issue_book(request):
    if request.method == 'POST':
        book_id = request.POST.get('book')
        student_id = request.POST.get('student')
        book = get_object_or_404(Book, pk=book_id)
        student = get_object_or_404(Student, pk=student_id)

        if book.available_copies < 1:
            messages.error(request, f'No copies of "{book.title}" available.')
            return redirect('issue_book')

        IssueRecord.objects.create(book=book, student=student)
        book.available_copies -= 1
        book.save()
        messages.success(request, f'"{book.title}" issued to {student.name}.')
        return redirect('issue_list')

    books = Book.objects.filter(available_copies__gt=0)
    students = Student.objects.all()
    return render(request, 'library/issue_form.html', {'books': books, 'students': students})


def return_book(request, pk):
    record = get_object_or_404(IssueRecord, pk=pk)
    if record.status == 'ISSUED':
        record.status = 'RETURNED'
        record.return_date = timezone.now().date()
        record.save()

        book = record.book
        book.available_copies += 1
        book.save()
        messages.success(request, f'"{book.title}" returned by {record.student.name}.')
    return redirect('issue_list')
