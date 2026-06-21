from django.urls import path
from . import views

urlpatterns = [
    path('',                      views.HomeView.as_view(),              name='ids-home'),
    path('monitor/',              views.SnifferMonitorView.as_view(),    name='ids-monitor'),
    path('history/',              views.HistoryView.as_view(),           name='ids-history'),
    path('about/',                views.AboutView.as_view(),             name='ids-about'),
    path('api/sniffer/predict/',  views.SnifferPredictionView.as_view(), name='ids-sniffer-predict'),
    path('api/sniffer/status/',   views.SnifferStatusView.as_view(),     name='ids-sniffer-status'),
    path('api/sniffer/start/',    views.SnifferStartView.as_view(),      name='ids-sniffer-start'),
    path('api/sniffer/stop/',     views.SnifferStopView.as_view(),       name='ids-sniffer-stop'),
]
