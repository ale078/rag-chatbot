class OllamaUnavailable(Exception):
    """Ollama or a requested local model cannot be used."""


class DocumentProcessingError(Exception):
    """A supported document could not be extracted or indexed."""
