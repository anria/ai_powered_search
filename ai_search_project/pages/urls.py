from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('chapter/<int:chapter_id>/', views.chapter, name='chapter'),
    path('search/', views.search, name='search'),  # for iframe results
]