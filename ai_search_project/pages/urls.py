from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('chapter/<int:chapter_id>/', views.chapter, name='chapter'),
    path('search/', views.search, name='search'),  # for iframe results
    path('api/chat/', views.chat, name='chat'),   # <-- new 9/25/2026
    path('api/feedback/', views.feedback, name='feedback'),
    path('judgements/', views.judgements, name='judgements'),
    path('api/judgements/', views.judgements_data, name='judgements_data'),
    path('api/judgements/<int:idx>/', views.judgement_update, name='judgement_update'),
    path('api/judgements/<int:idx>/notes/', views.judgement_notes, name='judgement_notes'),
]