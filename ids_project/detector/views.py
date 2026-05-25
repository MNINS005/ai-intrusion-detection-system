"""
detector/views.py
──────────────────
Thin views:
- HTTP request handling
- validation
- response handling

Business logic lives in services.py
"""

import logging

from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.shortcuts import render

from .forms import NetworkRecordForm
from .mixins import StaffRequiredMixin, PipelineCheckMixin
from .models import PredictionLog, PredictionFeatures, ModelVersion
from .services import (
    run_prediction,
    run_training_pipeline,
    get_pipeline
)

from src.constants import (
    CLASS_NAMES,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Home View
# ─────────────────────────────────────────────────────────────

class HomeView(TemplateView):

    template_name = "detector/home.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["model_loaded"] = get_pipeline() is not None

        context["total_predictions"] = (
            PredictionLog.objects.count()
        )

        context["active_model"] = (
            ModelVersion.objects
            .filter(is_active=True)
            .first()
        )

        context["class_names"] = CLASS_NAMES

        return context


# ─────────────────────────────────────────────────────────────
# Prediction View
# ─────────────────────────────────────────────────────────────

class PredictView(PipelineCheckMixin, View):

    template_name = "detector/predict.html"

    def get(self, request):

        form = NetworkRecordForm()

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "model_loaded": get_pipeline() is not None,
            }
        )

    def post(self, request):

        form = NetworkRecordForm(request.POST)

        if not form.is_valid():

            return JsonResponse(
                {
                    "status": "error",
                    "errors": form.errors,
                },
                status=400,
            )

        try:

            result = run_prediction(form.cleaned_data)

            return JsonResponse(result.to_dict())

        except Exception as e:

            logger.exception("Prediction failed.")

            return JsonResponse(
                {
                    "status": "error",
                    "message": str(e),
                },
                status=500,
            )


# ─────────────────────────────────────────────────────────────
# Training View (Staff Only)
# ─────────────────────────────────────────────────────────────

class TrainView(StaffRequiredMixin, View):

    """
    Restricted training endpoint.

    In production:
    - move to Celery/background worker
    - avoid public access
    """

    def post(self, request):

        try:

            metrics = run_training_pipeline()

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Training completed.",

                    "metrics": {
                        "accuracy": metrics.get("accuracy"),
                        "f1_weighted": metrics.get("f1_weighted"),
                    },
                }
            )

        except Exception as e:

            logger.exception("Training failed.")

            return JsonResponse(
                {
                    "status": "error",
                    "message": str(e),
                },
                status=500,
            )


# ─────────────────────────────────────────────────────────────
# Prediction History
# ─────────────────────────────────────────────────────────────

class HistoryView(ListView):

    model = PredictionLog

    template_name = "detector/history.html"

    context_object_name = "logs"

    ordering = ["-created_at"]

    paginate_by = 20

    def get_queryset(self):

        queryset = super().get_queryset()

        cls_filter = self.request.GET.get("class")

        if (
            cls_filter and
            cls_filter in CLASS_NAMES.values()
        ):
            queryset = queryset.filter(
                predicted_class=cls_filter
            )

        return queryset

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["class_names"] = CLASS_NAMES

        context["total"] = (
            PredictionLog.objects.count()
        )

        context["active_filter"] = (
            self.request.GET.get("class", "")
        )

        return context


# ─────────────────────────────────────────────────────────────
# Prediction Detail View
# ─────────────────────────────────────────────────────────────

class PredictionDetailView(DetailView):

    model = PredictionLog

    template_name = "detector/prediction_detail.html"

    context_object_name = "log"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["features"] = self._get_features()

        context["feature_fields"] = (
            CATEGORICAL_FEATURES +
            NUMERICAL_FEATURES
        )

        return context

    def _get_features(self):

        try:

            return self.object.predictionfeatures

        except PredictionFeatures.DoesNotExist:

            return None

# Create your views here.
