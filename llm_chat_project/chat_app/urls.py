from django.urls import path 
from . import views 
 
urlpatterns = [ 
    path('', views.chat_page, name='chat_page'), 
    path('query/', views.process_query, name='process_query'), 
]