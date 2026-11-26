"""Visualización de árboles sintácticos del parser del español.

Dibuja el árbol que produce parser_es.py como imagen PNG usando matplotlib
(no necesita instalar Graphviz en el sistema). También puede exportar el árbol
en formato DOT (Graphviz) o en notación de corchetes (nltk.Tree).

Colores de los nodos:
    gris claro  no terminales (oracion, sn, sv, ...)
    azul        categorías léxicas (DET, N, V, ...)
    sin caja    las palabras

Uso:
    python arbol_es.py "La niña come una manzana roja ."
    python arbol_es.py "La niña come una manzana roja ." -o arbol.png
    python arbol_es.py "La niña come ." --dot              (imprime DOT)
    python arbol_es.py oraciones.txt -d arboles/           (un PNG por oración)

Requiere: pip install matplotlib
"""
import argparse
import re
import sys
from pathlib import Path

from lexer_es import ErrorLexico
from parser_es import ErrorSintactico, analizar

COLOR_NO_TERMINAL = "#e8e8e8"
COLOR_CATEGORIA = "#cfe2f3"


# ------------------------------------------------------------------ disposición
def _posiciones(arbol):
    """Calcula (x, y) de cada nodo. Las hojas se reparten de izquierda a
    derecha; cada nodo interno queda centrado sobre sus hijos."""
    pos = {}
    siguiente_x = [0]

    def recorrer(nodo, profundidad):
        if nodo.es_hoja():
            pos[id(nodo)] = (siguiente_x[0], -profundidad)
            siguiente_x[0] += 1
            return
        for hijo in nodo.hijos:
            recorrer(hijo, profundidad + 1)
        xs = [pos[id(h)][0] for h in nodo.hijos]
        pos[id(nodo)] = ((min(xs) + max(xs)) / 2, -profundidad)

    recorrer(arbol, 0)
    return pos


def _profundidad(nodo):
    if nodo.es_hoja():
        return 1
    return 1 + max(_profundidad(h) for h in nodo.hijos)


# ---------------------------------------------------------------------- dibujo
def dibujar(arbol, titulo=None, archivo=None, mostrar=False):
    import matplotlib
    if not mostrar:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pos = _posiciones(arbol)
    n_hojas = len(arbol.hojas())
    prof = _profundidad(arbol)
    # Las palabras se dibujan un nivel debajo de la hoja más profunda.
    y_palabras = -prof

    fig, ax = plt.subplots(figsize=(max(6, 1.25 * n_hojas), max(4, 0.85 * (prof + 1))))
    ax.axis("off")

    def caja(x, y, texto, color):
        ax.text(x, y, texto, ha="center", va="center", fontsize=10, zorder=3,
                bbox=dict(boxstyle="round,pad=0.3", fc=color, ec="#555555", lw=0.8))

    def recorrer(nodo):
        x, y = pos[id(nodo)]
        if nodo.es_hoja():
            caja(x, y, nodo.nombre, COLOR_CATEGORIA)
            ax.plot([x, x], [y, y_palabras], color="#999999", lw=0.8, ls=":", zorder=1)
            ax.text(x, y_palabras, nodo.token.valor, ha="center", va="center",
                    fontsize=11, fontstyle="italic", zorder=3)
            return
        caja(x, y, nodo.nombre, COLOR_NO_TERMINAL)
        for hijo in nodo.hijos:
            hx, hy = pos[id(hijo)]
            ax.plot([x, hx], [y, hy], color="#555555", lw=1, zorder=1)
            recorrer(hijo)

    recorrer(arbol)
    ax.set_xlim(-0.8, n_hojas - 0.2)
    ax.set_ylim(y_palabras - 0.6, 0.6)
    if titulo:
        ax.set_title(titulo, fontsize=12)
    fig.tight_layout()

    if archivo:
        fig.savefig(archivo, dpi=150)
    if mostrar:
        plt.show()
    plt.close(fig)


def a_dot(arbol):
    """Devuelve el árbol en formato DOT (para Graphviz)."""
    lineas = ["digraph arbol {", '  node [fontname="Helvetica"];']
    contador = [0]

    def recorrer(nodo):
        mi_id = f"n{contador[0]}"
        contador[0] += 1
        if nodo.es_hoja():
            lineas.append(f'  {mi_id} [label="{nodo.nombre}", shape=box, '
                          f'style=filled, fillcolor="{COLOR_CATEGORIA}"];')
            palabra = f"{mi_id}p"
            lineas.append(f'  {palabra} [label="{nodo.token.valor}", shape=plaintext];')
            lineas.append(f"  {mi_id} -> {palabra};")
        else:
            lineas.append(f'  {mi_id} [label="{nodo.nombre}", shape=box, '
                          f'style="rounded,filled", fillcolor="{COLOR_NO_TERMINAL}"];')
            for hijo in nodo.hijos:
                lineas.append(f"  {mi_id} -> {recorrer(hijo)};")
        return mi_id

    recorrer(arbol)
    lineas.append("}")
    return "\n".join(lineas)


# ---------------------------------------------------------------------- CLI
def _nombre_archivo(oracion, i):
    base = re.sub(r"[^\w]+", "_", oracion.lower()).strip("_")[:40]
    return f"{i:02d}_{base}.png"


def main():
    ap = argparse.ArgumentParser(description="Dibuja árboles sintácticos del español.")
    ap.add_argument("entrada", nargs="+", help="oración entre comillas, o archivo .txt")
    ap.add_argument("-o", "--salida", help="archivo PNG (una sola oración)")
    ap.add_argument("-d", "--directorio", help="carpeta para un PNG por oración")
    ap.add_argument("--dot", action="store_true", help="imprimir el árbol en DOT")
    ap.add_argument("--corchetes", action="store_true",
                    help="imprimir el árbol en notación de corchetes (nltk)")
    args = ap.parse_args()

    ruta = Path(args.entrada[0])
    if len(args.entrada) == 1 and ruta.is_file():
        oraciones = [l.strip() for l in ruta.read_text(encoding="utf-8").splitlines()
                     if l.strip() and not l.lstrip().startswith("#")]
    else:
        oraciones = [" ".join(args.entrada)]

    if args.directorio:
        Path(args.directorio).mkdir(parents=True, exist_ok=True)

    errores = 0
    for i, oracion in enumerate(oraciones, 1):
        try:
            arbol = analizar(oracion)
        except (ErrorLexico, ErrorSintactico) as e:
            tipo = "léxico" if isinstance(e, ErrorLexico) else "sintáctico"
            print(f"[RECHAZADA] {oracion}\n   Error {tipo}: {e}")
            errores += 1
            continue

        if args.dot:
            print(a_dot(arbol))
        elif args.corchetes:
            print(arbol.corchetes())
        elif args.directorio:
            archivo = Path(args.directorio) / _nombre_archivo(oracion, i)
            dibujar(arbol, titulo=oracion, archivo=archivo)
            print(f"[ACEPTADA]  {oracion}\n   -> {archivo}")
        elif args.salida:
            dibujar(arbol, titulo=oracion, archivo=args.salida)
            print(f"Árbol guardado en {args.salida}")
        else:
            dibujar(arbol, titulo=oracion, mostrar=True)
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
