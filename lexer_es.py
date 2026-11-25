"""Analizador léxico para el subconjunto controlado del español (Fase 2).

Igual que lexer.py de la Fase 1, reconoce los tokens con expresiones regulares
(lenguaje regular, tipo 3). La diferencia es que aquí el tipo del token no sale
de la forma de la palabra sino de una búsqueda en el léxico (lexico_es.py):
"perro" y "corre" tienen la misma forma (letras), pero son N y V.

Cada token lleva:
    tipo    categoría gramatical (DET, N, V, ...), el terminal de la gramática
    valor   la palabra tal como aparece en el texto
    rasgos  lista de análisis posibles del léxico (género, número, persona...)
    linea, columna

Uso:
    python lexer_es.py "El perro come una manzana ."
    python lexer_es.py archivo.txt        (una oración por línea)
"""
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from lexico_es import buscar


@dataclass
class Token:
    tipo: str
    valor: str
    linea: int
    columna: int
    rasgos: list = field(default_factory=list)

    def __repr__(self):
        return f"Token({self.tipo}, {self.valor!r}, {self.linea}:{self.columna})"


class ErrorLexico(Exception):
    pass


# Una palabra: letras del español (con tildes, ñ y ü). El punto final y los
# signos ¿ ? ¡ ! , son tokens aparte. Cualquier otro carácter es un error.
ESPECIFICACION = [
    ("ESPACIO", r"[ \t]+"),
    ("SALTO", r"\n"),
    ("PALABRA", r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+"),
    ("PUNTO", r"\."),
    ("SIGNO", r"[¿?¡!,]"),      # en el léxico, pero fuera de la gramática
    ("ERROR", r"."),
]
PATRON = re.compile("|".join(f"(?P<{n}>{p})" for n, p in ESPECIFICACION))


def tokenizar(texto):
    """Convierte `texto` en una lista de tokens terminada en EOF."""
    tokens = []
    linea, inicio_linea = 1, 0
    for m in PATRON.finditer(texto):
        clase, lexema = m.lastgroup, m.group()
        columna = m.start() - inicio_linea + 1
        if clase == "ESPACIO":
            continue
        if clase == "SALTO":
            linea, inicio_linea = linea + 1, m.end()
            continue
        if clase == "ERROR":
            raise ErrorLexico(f"Línea {linea}, columna {columna}: "
                              f"carácter no válido {lexema!r}")
        analisis = buscar(lexema)
        if not analisis:
            raise ErrorLexico(f"Línea {linea}, columna {columna}: "
                              f"la palabra {lexema!r} no está en el vocabulario")
        categorias = {a["cat"] for a in analisis}
        if len(categorias) > 1:
            # El léxico actual no tiene palabras de dos categorías; si se agrega
            # una (p. ej. "mañana" como N y ADV), el lexer no podría decidir.
            raise ErrorLexico(f"Línea {linea}, columna {columna}: {lexema!r} es "
                              f"ambigua entre {sorted(categorias)}")
        tokens.append(Token(categorias.pop(), lexema, linea, columna, analisis))
    tokens.append(Token("EOF", "", linea, len(texto) - inicio_linea + 1))
    return tokens


def describir_rasgos(analisis):
    """Texto corto con los rasgos de un análisis: 'm s', '3 p preterito', ..."""
    claves = ("gen", "num", "per", "tiempo", "trans")
    return " ".join(str(analisis[k]) for k in claves if k in analisis)


def _leer_entrada(argv):
    if len(argv) > 1:
        ruta = Path(argv[1])
        return ruta.read_text(encoding="utf-8") if ruta.is_file() else " ".join(argv[1:])
    return "La pequeña niña come una manzana roja en el jardín ."


if __name__ == "__main__":
    texto = _leer_entrada(sys.argv)
    try:
        tokens = tokenizar(texto)
    except ErrorLexico as e:
        print(f"Error léxico: {e}")
        sys.exit(1)
    print(f"{'LÍN:COL':8} {'TIPO':6} {'LEXEMA':14} RASGOS")
    for t in tokens:
        rasgos = " | ".join(describir_rasgos(a) for a in t.rasgos)
        print(f"{t.linea:>3}:{t.columna:<4} {t.tipo:6} {t.valor!r:14} {rasgos}")
