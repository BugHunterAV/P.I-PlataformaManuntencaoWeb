"""
Utilitário para exportação de dados em formato CSV.
"""
import csv
from django.http import HttpResponse


def exportar_csv(nome_arquivo, colunas, linhas):
    """
    Gera um HttpResponse com conteúdo CSV pronto para download.

    Args:
        nome_arquivo (str): Nome do arquivo sem extensão. Ex: 'ordens_servico'
        colunas (list[str]): Lista de cabeçalhos. Ex: ['ID', 'Título', 'Status']
        linhas (list[list]): Lista de listas com os valores de cada linha.

    Returns:
        HttpResponse com Content-Type text/csv e Content-Disposition attachment.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}.csv"'

    # BOM para Excel reconhecer acentos corretamente
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(colunas)

    for linha in linhas:
        writer.writerow(linha)

    return response
