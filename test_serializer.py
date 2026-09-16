import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from manutencao.models import OrdemServico
from accounts.models import Usuario
from manutencao.serializers import OrdemServicoSerializer
from rest_framework.request import Request
from django.test import RequestFactory

tecnico = Usuario.objects.filter(tipo_usuario='tecnico').first()
os_obj = OrdemServico.objects.get(id=162)

factory = RequestFactory()
request = factory.patch(f'/api/ordens-servico/{os_obj.id}/')
request.user = tecnico
# Wrap request
from rest_framework.request import Request
drf_request = Request(request)

serializer = OrdemServicoSerializer(os_obj, data={'responsavel': tecnico.id, 'status': 'andamento'}, partial=True, context={'request': drf_request})
if not serializer.is_valid():
    print("ERRORS:", serializer.errors)
else:
    print("VALID:", serializer.validated_data)
