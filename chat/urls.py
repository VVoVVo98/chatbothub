from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
]