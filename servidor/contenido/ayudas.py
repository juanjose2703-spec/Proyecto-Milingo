"""Ayudas para escribir preguntas sin repetir código.

op(correcta, *distractores)  -> opciones de selección (una correcta).
aceptadas(*textos)           -> respuestas escritas válidas (todas correctas).
fichas(*palabras)            -> palabras en el ORDEN CORRECTO (el servidor las mezcla).
"""


def op(correcta, *distractores):
    return [(correcta, True)] + [(d, False) for d in distractores]


def aceptadas(*textos):
    return [(t, True) for t in textos]


def fichas(*palabras):
    return [(p, True) for p in palabras]