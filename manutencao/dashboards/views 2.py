from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg, F, ExpressionWrapper, fields
from django.utils import timezone
from manutencao.models import OrdemServico
from ativos.models import Equipamento
from datetime import timedelta

class KpiDashboardView(APIView):
    def get(self, request, *args, **kwargs):
        equipamento_id = request.query_params.get('equipamento_id')
        
        # Filtro base
        os_queryset = OrdemServico.objects.filter(status='concluida')
        if equipamento_id:
            os_queryset = os_queryset.filter(equipamento_id=equipamento_id)
            equipamentos = Equipamento.objects.filter(id=equipamento_id)
        else:
            equipamentos = Equipamento.objects.all()

        results = []

        for eq in equipamentos:
            os_eq = os_queryset.filter(equipamento=eq).order_by('data_abertura')
            
            # 1. MTTR (Mean Time To Repair)
            # Média de (data_conclusao - data_abertura)
            mttr_data = os_eq.annotate(
                duration=ExpressionWrapper(F('data_conclusao') - F('data_abertura'), output_field=fields.DurationField())
            ).aggregate(avg_mttr=Avg('duration'))
            
            mttr = mttr_data['avg_mttr'] if mttr_data['avg_mttr'] else timedelta(0)

            # 2. MTBF (Mean Time Between Failures)
            # Média do tempo entre o fim de uma OS e o início da próxima
            inter_failure_times = []
            last_conclusao = None
            for os in os_eq:
                if last_conclusao:
                    inter_failure_times.append(os.data_abertura - last_conclusao)
                last_conclusao = os.data_conclusao
            
            if inter_failure_times:
                mtbf = sum(inter_failure_times, timedelta(0)) / len(inter_failure_times)
            else:
                mtbf = timedelta(0)

            # 3. Disponibilidade (Availability %)
            # Fórmula: MTBF / (MTBF + MTTR) * 100
            total_time = mtbf + mttr
            if total_time.total_seconds() > 0:
                disponibilidade = (mtbf.total_seconds() / total_time.total_seconds()) * 100
            else:
                disponibilidade = 100.0 if eq.status == 'ativo' else 0.0

            results.append({
                'equipamento': eq.nome,
                'equipamento_id': eq.id,
                'mttr_hours': round(mttr.total_seconds() / 3600, 2),
                'mtbf_hours': round(mtbf.total_seconds() / 3600, 2),
                'disponibilidade_porcentagem': round(disponibilidade, 2),
                'total_manutencoes': os_eq.count()
            })

        return Response(results)
