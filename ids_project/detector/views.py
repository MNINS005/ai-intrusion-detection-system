import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncHour
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .forms import PredictionForm
from .models import PredictionLog

from src.pipeline.prediction_pipeline import PredictPipeline, CustomData


# ─────────────────────────────────────────────────────────────────
# Pipeline loaded once at startup — not on every request
# ─────────────────────────────────────────────────────────────────

pipeline = PredictPipeline()


DEFAULT_NETWORK_FEATURES = {
    'duration': 0,
    'land': 0,
    'wrong_fragment': 0,
    'urgent': 0,
    'hot': 0,
    'num_failed_logins': 0,
    'logged_in': 1,
    'num_compromised': 0,
    'root_shell': 0,
    'su_attempted': 0,
    'num_root': 0,
    'num_file_creations': 0,
    'num_shells': 0,
    'num_access_files': 0,
    'num_outbound_cmds': 0,
    'is_host_login': 0,
    'is_guest_login': 0,
    'count': 0,
    'srv_count': 0,
    'serror_rate': 0.0,
    'srv_serror_rate': 0.0,
    'rerror_rate': 0.0,
    'srv_rerror_rate': 0.0,
    'same_srv_rate': 1.0,
    'diff_srv_rate': 0.0,
    'srv_diff_host_rate': 0.0,
    'dst_host_count': 0,
    'dst_host_srv_count': 0,
    'dst_host_same_srv_rate': 1.0,
    'dst_host_diff_srv_rate': 0.0,
    'dst_host_same_src_port_rate': 0.0,
    'dst_host_srv_diff_host_rate': 0.0,
    'dst_host_serror_rate': 0.0,
    'dst_host_srv_serror_rate': 0.0,
    'dst_host_rerror_rate': 0.0,
    'dst_host_srv_rerror_rate': 0.0,
}


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def get_chart_data():
    qs = (
        PredictionLog.objects
        .filter(predicted_class='Anomaly')
        .annotate(hour=TruncHour('created_at'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    labels = [entry['hour'].strftime('%d %b %H:%M') for entry in qs]
    counts = [entry['count'] for entry in qs]
    return labels, counts  # return plain lists, not json.dumps()


def predict_and_log_traffic(payload):
    features = {
        **DEFAULT_NETWORK_FEATURES,
        'protocol_type': payload['protocol_type'],
        'service': payload['service'],
        'flag': payload['flag'],
        'src_bytes': float(payload['src_bytes']),
        'dst_bytes': float(payload['dst_bytes']),
    }

    df = CustomData(**features).get_data_as_dataframe()
    predicted_label = int(pipeline.predict(df)[0])
    predicted_class = 'Anomaly' if predicted_label == 1 else 'Normal'

    PredictionLog.objects.create(
        protocol_type=features['protocol_type'],
        service=features['service'],
        flag=features['flag'],
        src_bytes=features['src_bytes'],
        dst_bytes=features['dst_bytes'],
        predicted_label=predicted_label,
        predicted_class=predicted_class,
    )

    return predicted_label, predicted_class

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
                _, predicted_class = predict_and_log_traffic(form.cleaned_data)

                context = {
                    'form':   form,
                    'result': predicted_class,
                    'title':  'Home',
                }
                return render(request, self.template_name, context)

            except Exception as e:
                messages.error(request, f'Prediction failed: {e}')

        return render(request, self.template_name, {'form': form, 'title': 'Home'})


@method_decorator(csrf_exempt, name='dispatch')
class SnifferPredictionView(View):
    """Accepts traffic summaries from the local Scapy sniffer."""

    http_method_names = ['post']
    required_fields = {'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes'}

    def post(self, request):
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

        missing = sorted(self.required_fields - set(payload))
        if missing:
            return JsonResponse({'error': 'Missing required fields.', 'fields': missing}, status=400)

        try:
            predicted_label, predicted_class = predict_and_log_traffic(payload)
        except (TypeError, ValueError) as exc:
            return JsonResponse({'error': f'Invalid traffic values: {exc}'}, status=400)
        except Exception as exc:
            return JsonResponse({'error': f'Prediction failed: {exc}'}, status=500)

        return JsonResponse({
            'predicted_label': predicted_label,
            'predicted_class': predicted_class,
        })


class HistoryView(View):
    """All past predictions newest first + anomaly over time line chart."""

    template_name = 'detector/history.html'

    def get(self, request):
        logs                  = PredictionLog.objects.order_by('-created_at')
        total                 = logs.count()
        anomaly_count         = logs.filter(predicted_class='Anomaly').count()
        normal_count          = total - anomaly_count
        chart_labels, chart_counts = get_chart_data()

        context = {
            'logs':         logs,
            'total':        total,
            'anomaly_count': anomaly_count,
            'normal_count':  normal_count,
            'chart_labels':  chart_labels,
            'chart_counts':  chart_counts,
            'title':        'History',
        }
        return render(request, self.template_name, context)


class AboutView(View):
    """Static about page."""

    template_name = 'detector/about.html'

    def get(self, request):
        return render(request, self.template_name, {'title': 'About'})
