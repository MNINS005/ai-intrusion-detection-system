from django.db import models
import datetime


# Create your models here.
class PredictionLog(models.Model):
    protocol_type = models.CharField(max_length=50)
    service = models.CharField(max_length=50)
    flag              = models.CharField(max_length=10)
    src_bytes         = models.FloatField()
    dst_bytes         = models.FloatField()
    predicted_label   = models.IntegerField()
    predicted_class   = models.CharField(max_length=20)
    created_at        = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.created_at} | {self.predicted_class}"