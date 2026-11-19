"""Analizador léxico (lexer) para un subconjunto de C++.

Nivel en la jerarquía de Chomsky: lenguajes REGULARES (tipo 3).
Cada clase de token se describe con una expresión regular, y todas se unen
en un solo patrón. Python prueba las alternativas en orden, así que las más
específicas van primero (por ejemplo '==' antes que '=').

Uso:  python lexer.py [archivo.cpp]
"""
from dataclasses import dataclass
from pathlib import Path
import re
import sys

PALABRAS_RESERVADAS = {
    "using", "namespace", "std", "iostream", "main",
    "int", "float", "bool", "void",
    "if", "else", "while", "do", "for", "return",
    "switch", "case", "default", "break",
    "true", "false",
}

# Especificación formal de los tokens: (nombre, expresión regular)
ESPECIFICACION = [
    ("COMENTARIO",     r"//[^\n]*|/\*[\s\S]*?\*/"),
    ("COMENTARIO_MAL", r"/\*"),                        # '/*' que nunca se cierra
    ("ESPACIO",        r"\s+"),
    ("INCLUDE",        r"\#include\b"),
    ("NUM",            r"\d[\w.]*"),                    # todo lo que empieza con dígito
    ("ID",             r"[A-Za-z_]\w*"),                # identificadores y reservadas
    ("OPERADOR",       r"==|!=|<=|>=|&&|\|\||\+\+|--|[+\-*/%<>=!]"),
    ("DELIMITADOR",    r"[(){};,:]"),
    ("ERROR",          r"."),                           # cualquier otro carácter
]
PATRON = re.compile("|".join(f"(?P<{n}>{r})" for n, r in ESPECIFICACION))
NUM_VALIDO = re.compile(r"\d+(\.\d+)?")   # entero (42) o real (3.14)


@dataclass
class Token:
    tipo: str     # categoría que usan el parser y el semántico
    valor: str    # lexema: el texto exacto del código
    linea: int
    columna: int


class ErrorLexico(Exception):
    pass


def tokenizar(codigo: str) -> list[Token]:
    tokens = []
    linea, inicio_linea = 1, 0  

    for m in PATRON.finditer(codigo):
        clase, valor = m.lastgroup, m.group()
        columna = m.start() - inicio_linea + 1

        if clase == "ERROR":
            raise ErrorLexico(f"Línea {linea}, columna {columna}: carácter no válido {valor!r}")
        if clase == "NUM" and not NUM_VALIDO.fullmatch(valor):   # 12abc, 3., 1.2.3
            raise ErrorLexico(f"Línea {linea}, columna {columna}: número mal formado {valor!r}")
        if clase == "COMENTARIO_MAL":
            raise ErrorLexico(f"Línea {linea}, columna {columna}: comentario sin cerrar")

        if clase == "NUM":
            tokens.append(Token("NUM", valor, linea, columna))
        elif clase == "ID":
            # Una palabra reservada es su propio tipo; si no, es un identificador.
            tipo = valor if valor in PALABRAS_RESERVADAS else "ID"
            tokens.append(Token(tipo, valor, linea, columna))
        elif clase in ("INCLUDE", "OPERADOR", "DELIMITADOR"):
            tokens.append(Token(valor, valor, linea, columna))
        # ESPACIO y COMENTARIO se descartan

        # Si el lexema contenía saltos de línea, avanzamos el contador.
        if "\n" in valor:
            linea += valor.count("\n")
            inicio_linea = m.start() + valor.rindex("\n") + 1

    tokens.append(Token("EOF", "", linea, len(codigo) - inicio_linea + 1))
    return tokens


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "ejemplos" / "ejemplo.cpp"
    try:
        tokens = list(tokenizar(ruta.read_text(encoding="utf-8")))
    except ErrorLexico as e:
        print("Error léxico:", e)
        sys.exit(1)
    print(f"{'LÍN:COL':<8} {'TIPO':<10} LEXEMA")
    for t in tokens:
        print(f"{t.linea:>3}:{t.columna:<4} {t.tipo:<10} {t.valor!r}")
