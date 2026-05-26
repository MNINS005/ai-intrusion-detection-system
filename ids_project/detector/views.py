from django.shortcuts import render
from django.views import View
from django.contrib import messages

from .forms import PredictionForm
from .models import PredictionLog

from src.pipeline.prediction_pipeline import PredictPipeline, CustomData


# ─────────────────────────────────────────────────────────────────
# Pipeline loaded once at startup — not on every request
# ─────────────────────────────────────────────────────────────────

pipeline = PredictPipeline()


# ─────────────────────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────────────────────

class HomeView(View):
    """
    GET  → empty prediction form
    POST → validate → predict → save to DB → show result
    """

    template_name = 'detector/home.html'

    def get(self, request):
        form = PredictionForm()
        return render(request, self.template_name, {'form': form, 'title': 'Home'})

    def post(self, request):
        form = PredictionForm(request.POST)

        if form.is_valid():
            try:
                # Build CustomData with user's 5 fields + safe defaults for the rest
                data = CustomData(
                    duration                    = 0,
                    protocol_type               = form.cleaned_data['protocol_type'],
                    service                     = form.cleaned_data['service'],
                    flag                        = form.cleaned_data['flag'],
                    src_bytes                   = form.cleaned_data['src_bytes'],
                    dst_bytes                   = form.cleaned_data['dst_bytes'],
                    land                        = 0,
                    wrong_fragment              = 0,
                    urgent                      = 0,
                    hot                         = 0,
                    num_failed_logins           = 0,
                    logged_in                   = 1,
                    num_compromised             = 0,
                    root_shell                  = 0,
                    su_attempted                = 0,
                    num_root                    = 0,
                    num_file_creations          = 0,
                    num_shells                  = 0,
                    num_access_files            = 0,
                    num_outbound_cmds           = 0,
                    is_host_login               = 0,
                    is_guest_login              = 0,
                    count                       = 0,
                    srv_count                   = 0,
                    serror_rate                 = 0.0,
                    srv_serror_rate             = 0.0,
                    rerror_rate                 = 0.0,
                    srv_rerror_rate             = 0.0,
                    same_srv_rate               = 1.0,
                    diff_srv_rate               = 0.0,
                    srv_diff_host_rate          = 0.0,
                    dst_host_count              = 0,
                    dst_host_srv_count          = 0,
                    dst_host_same_srv_rate      = 1.0,
                    dst_host_diff_srv_rate      = 0.0,
                    dst_host_same_src_port_rate = 0.0,
                    dst_host_srv_diff_host_rate = 0.0,
                    dst_host_serror_rate        = 0.0,
                    dst_host_srv_serror_rate    = 0.0,
                    dst_host_rerror_rate        = 0.0,
                    dst_host_srv_rerror_rate    = 0.0,
                )

                df              = data.get_data_as_dataframe()
                predicted_label = int(pipeline.predict(df)[0])

                # Isolation Forest: -1 = anomaly, 1 = normal
                predicted_class = 'Anomaly' if predicted_label == 1 else 'Normal'

                PredictionLog.objects.create(
                    protocol_type   = form.cleaned_data['protocol_type'],
                    service         = form.cleaned_data['service'],
                    flag            = form.cleaned_data['flag'],
                    src_bytes       = form.cleaned_data['src_bytes'],
                    dst_bytes       = form.cleaned_data['dst_bytes'],
                    predicted_label = predicted_label,
                    predicted_class = predicted_class,
                )

                context = {
                    'form':   form,
                    'result': predicted_class,
                    'title':  'Home',
                }
                return render(request, self.template_name, context)

            except Exception as e:
                messages.error(request, f'Prediction failed: {e}')

        return render(request, self.template_name, {'form': form, 'title': 'Home'})


class HistoryView(View):
    """All past predictions, newest first."""

    template_name = 'detector/history.html'

    def get(self, request):
        logs = PredictionLog.objects.order_by('-created_at')
        return render(request, self.template_name, {'logs': logs, 'title': 'History'})


class AboutView(View):
    """Static about page."""

    template_name = 'detector/about.html'

    def get(self, request):
        return render(request, self.template_name, {'title': 'About'})