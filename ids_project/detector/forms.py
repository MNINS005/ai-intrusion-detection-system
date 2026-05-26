from django import forms


PROTOCOL_CHOICES = [
    ('tcp',  'TCP'),
    ('udp',  'UDP'),
    ('icmp', 'ICMP'),
]

SERVICE_CHOICES = [
    ('http',   'HTTP'),
    ('ftp',    'FTP'),
    ('smtp',   'SMTP'),
    ('ssh',    'SSH'),
    ('dns',    'DNS'),
    ('other',  'Other'),
]

FLAG_CHOICES = [
    ('SF',   'SF  — Normal'),
    ('S0',   'S0  — No response'),
    ('REJ',  'REJ — Rejected'),
    ('RSTO', 'RSTO — Reset by originator'),
    ('RSTR', 'RSTR — Reset by responder'),
    ('SH',   'SH  — Half-open'),
]


class PredictionForm(forms.Form):
    """
    Collects the 5 features stored in PredictionLog.
    Categorical fields use dropdowns; byte fields use number inputs.
    """

    protocol_type = forms.ChoiceField(
        choices=PROTOCOL_CHOICES,
        label='Protocol Type',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    service = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        label='Service',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    flag = forms.ChoiceField(
        choices=FLAG_CHOICES,
        label='Connection Flag',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    src_bytes = forms.FloatField(
        min_value=0,
        label='Source Bytes',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        help_text='Bytes sent from source to destination.',
    )

    dst_bytes = forms.FloatField(
        min_value=0,
        label='Destination Bytes',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        help_text='Bytes sent from destination to source.',
    )