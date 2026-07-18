from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/delete/<int:pk>/', views.book_delete, name='book_delete'),

    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/delete/<int:pk>/', views.student_delete, name='student_delete'),

    path('issues/', views.issue_list, name='issue_list'),
    path('issues/issue/', views.issue_book, name='issue_book'),
    path('issues/return/<int:pk>/', views.return_book, name='return_book'),
]
