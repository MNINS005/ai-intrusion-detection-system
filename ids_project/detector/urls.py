
from django.urls import path
from .views import (
    HomeView,
    TrainView,
    PredictView,
    BatchPredictView,
    HistoryView,
    PredictionDetailView,
)
 
urlpatterns = [
    path("",                  HomeView.as_view(),          name="home"),
    path("train/",            TrainView.as_view(),          name="train"),
    path("predict/",          PredictView.as_view(),        name="predict"),
    path("predict/batch/",    BatchPredictView.as_view(),   name="predict-batch"),
    path("history/",          HistoryView.as_view(),        name="history"),
    path("history/<int:pk>/", PredictionDetailView.as_view(), name="prediction-detail"),
]