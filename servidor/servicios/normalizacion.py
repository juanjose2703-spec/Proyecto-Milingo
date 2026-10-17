import re
import unicodedata


def normalizar(texto):
    """Prepara un texto para compararlo con las respuestas aceptadas.

    Ignora mayúsculas, tildes, apóstrofos, signos de puntuación y espacios sobrantes.
    "  ¡Hola,   AMIGO! " -> "hola amigo"
    """
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.casefold().replace("’", "'").replace("'", "")
    texto = re.sub(r"[^\w\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()