"""Casos de prueba del lexer y del analizador semántico.

Cada caso indica qué se espera: "ok", "lexico" (error léxico) o
"semantico" (error semántico). El script ejecuta todos, muestra el mensaje
obtenido y dice si coincide con lo esperado.

Uso:  python pruebas.py
"""
import sys
from lexer import ErrorLexico
from semantico import ErrorSemantico, analizar_codigo


def programa(cuerpo, extra=""):
    """Envuelve unas líneas dentro de main para no repetir código en cada caso."""
    return f"{extra}\nint main() {{\n{cuerpo}\n    return 0;\n}}"


CASOS = [
    # ---------------- válidos ----------------
    ("ok", "Declaraciones y expresiones", programa(
        "    int a = 5;\n    float b = a * 2.5;\n    bool c = a > 3 && !(b == 1.0);")),
    ("ok", "Ámbitos: misma variable en bloques distintos", programa(
        "    { int x = 1; }\n    { float x = 2.0; }")),
    ("ok", "Sombreado: x interna oculta a la externa", programa(
        "    int x = 1;\n    { bool x = true; }\n    x = x + 1;")),
    ("ok", "for, while, if/else y función", programa(
        "    int t = 0;\n    for (int i = 0; i < 3; i++) { t = t + doble(i); }\n"
        "    while (t > 0) t--;\n    if (t == 0) t = 1; else t = 2;",
        extra="int doble(int n) { return n * 2; }")),
    ("ok", "do-while con break", programa(
        "    int n = 10;\n    do {\n        n--;\n        if (n == 5) break;\n    } while (n > 0);")),
    ("ok", "switch con case, default y break", programa(
        "    int op = 2;\n    int r = 0;\n    switch (op) {\n        case 1: r = 10; break;\n"
        "        case -1: r = -10; break;\n        default: r = 0;\n    }")),

    # ---------------- errores léxicos ----------------
    ("lexico", "Carácter no válido '@'", programa("    int a = 3 @ 4;")),
    ("lexico", "Número mal formado '12abc'", programa("    int a = 12abc;")),
    ("lexico", "Número mal formado '1.2.3'", programa("    float a = 1.2.3;")),
    ("lexico", "Comentario sin cerrar", programa("    int a = 1; /* nunca se cierra")),

    # ---------------- errores semánticos ----------------
    ("semantico", "Variable no declarada", programa("    total = 5;")),
    ("semantico", "Redeclaración en el mismo ámbito", programa("    int x = 1;\n    int x = 2;")),
    ("semantico", "Asignar int a bool", programa("    bool activo = 4;")),
    ("semantico", "Asignar float a int", programa("    int n = 2.5;")),
    ("semantico", "Variable usada fuera de su ámbito", programa("    { int x = 2; }\n    x = 3;")),
    ("semantico", "Variable del for usada afuera", programa(
        "    for (int i = 0; i < 3; i++) { }\n    i = 5;")),
    ("semantico", "Suma entre int y bool", programa("    int a = 1 + true;")),
    ("semantico", "Condición no booleana", programa("    int a = 1;\n    if (a) a = 2;")),
    ("semantico", "Función con argumentos de menos", programa(
        "    int r = suma(1);", extra="int suma(int a, int b) { return a + b; }")),
    ("semantico", "Return de tipo incorrecto", "bool f() { return 3; }\nint main() { return 0; }"),
    ("semantico", "break fuera de ciclo o switch", programa("    int a = 1;\n    break;")),
    ("semantico", "Condición del do-while no booleana", programa(
        "    int n = 3;\n    do { n--; } while (n);")),
    ("semantico", "switch sobre un float", programa(
        "    float f = 1.5;\n    switch (f) { case 1: break; }")),
    ("semantico", "case repetido", programa(
        "    int op = 1;\n    switch (op) { case 1: break; case 1: break; }")),
    ("semantico", "default repetido", programa(
        "    int op = 1;\n    switch (op) { default: break; default: break; }")),
]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    aciertos = 0
    for esperado, titulo, codigo in CASOS:
        try:
            analizar_codigo(codigo)
            obtenido, mensaje = "ok", "sin errores"
        except ErrorLexico as e:
            obtenido, mensaje = "lexico", f"Error léxico: {e}"
        except ErrorSemantico as e:
            obtenido, mensaje = "semantico", f"Error semántico: {e}"
        bien = obtenido == esperado
        aciertos += bien
        print(f"[{'PASA' if bien else 'FALLA'}] {titulo}\n        -> {mensaje}")
    print(f"\n{aciertos}/{len(CASOS)} casos correctos")
