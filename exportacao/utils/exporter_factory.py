from .base_exporter import Exportador

class ExportadorFactory:
    _registro = {}

    @classmethod
    def registrar(cls, formato: str, exportador_cls: type):
        cls._registro[formato] = exportador_cls

    @classmethod
    def criar(cls, formato: str) -> Exportador:
        exportador_cls = cls._registro.get(formato)
        if not exportador_cls:
            raise ValueError(f"Formato de exportação '{formato}' não suportado.")
        return exportador_cls()
