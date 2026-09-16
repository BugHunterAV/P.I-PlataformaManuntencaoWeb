from abc import ABC, abstractmethod
from django.http import HttpResponse

class Exportador(ABC):
    @abstractmethod
    def exportar(self, nome: str, titulo: str, colunas: list, linhas: list) -> HttpResponse:
        pass
