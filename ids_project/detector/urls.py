from django.urls import path
from . import views

urlpatterns = [
    path('',                      views.HomeView.as_view(),              name='ids-home'),
    path('history/',              views.HistoryView.as_view(),           name='ids-history'),
    path('about/',                views.AboutView.as_view(),             name='ids-about'),
    path('api/sniffer/predict/',  views.SnifferPredictionView.as_view(), name='ids-sniffer-predict'),
]
