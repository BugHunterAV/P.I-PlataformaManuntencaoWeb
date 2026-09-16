class Prompt:
    def __init__(self, texto: str):
        self._texto = texto

    def obter_texto(self) -> str:
        return self._texto

    def __str__(self) -> str:
        return self._texto
