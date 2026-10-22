from django.contrib import admin
from .models import Alerta

@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('tipo_alerta', 'equipamento', 'sensor', 'origem', 'nivel', 'status', 'data_alerta')
    list_filter = ('origem', 'nivel', 'status', 'equipamento')
    search_fields = ('tipo_alerta', 'equipamento__nome', 'evento_chave')
