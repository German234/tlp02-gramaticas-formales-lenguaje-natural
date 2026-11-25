"""Parser descendente recursivo para el subconjunto controlado del español.

Implementa la gramática de docs/gramatica_espanol.bnf: una función por cada no
terminal. Lee los tokens que produce lexer_es.py y construye el árbol de
análisis sintáctico.

Los dos puntos donde la gramática no es LL(1) se resuelven así:

  1) <sps_nominales> (adjunción de la frase preposicional): regla codiciosa.
     Toda PREP/CONTR que aparece después de un sustantivo se une a ese
     sustantivo (adjunción baja), igual que el "else codicioso" de la Fase 1.

  2) <adjetivos> y <adverbios> con INT: se mira un token más (LL(2)).
     "muy" + ADJ pertenece al adjetivo; "muy" + ADV pertenece al adverbio.

Los nodos ε no se agregan al árbol para que el dibujo sea legible.

Uso:
    python parser_es.py "Juan mira al hombre con el telescopio ."
    python parser_es.py archivo.txt        (una oración por línea)
"""
import sys
from dataclasses import dataclass, field
from pathlib import Path

from lexer_es import ErrorLexico, tokenizar


@dataclass
class Nodo:
    """Nodo del árbol. Si `token` no es None, es una hoja (categoría + palabra)."""
    nombre: str
    hijos: list = field(default_factory=list)
    token: object = None

    def es_hoja(self):
        return self.token is not None

    def lineas(self, nivel=0):
        if self.es_hoja():
            yield "  " * nivel + f"{self.nombre} '{self.token.valor}'"
            return
        yield "  " * nivel + f"<{self.nombre}>"
        for hijo in self.hijos:
            yield from hijo.lineas(nivel + 1)

    def __str__(self):
        return "\n".join(self.lineas())

    def corchetes(self):
        """Notación con corchetes, compatible con nltk.Tree.fromstring()."""
        if self.es_hoja():
            return f"({self.nombre} {self.token.valor})"
        return f"({self.nombre} " + " ".join(h.corchetes() for h in self.hijos) + ")"

    def hojas(self):
        if self.es_hoja():
            return [self]
        return [h for hijo in self.hijos for h in hijo.hojas()]


class ErrorSintactico(Exception):
    pass


class Parser:
    INICIO_SN = {"DET", "NPROP"}
    INICIO_SP = {"PREP", "CONTR"}

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ----------------------------------------------------------- utilidades
    def ver(self, n=0):
        """Categoría del token actual (n=0) o del que está n posiciones después."""
        return self.tokens[min(self.pos + n, len(self.tokens) - 1)].tipo

    def consumir(self, tipo):
        token = self.tokens[self.pos]
        if token.tipo != tipo:
            self.error(f"se esperaba {tipo}")
        self.pos += 1
        return Nodo(tipo, token=token)

    def error(self, esperado):
        token = self.tokens[self.pos]
        encontrado = repr(token.valor) if token.tipo != "EOF" else "el fin del texto"
        raise ErrorSintactico(f"Línea {token.linea}, columna {token.columna}: "
                              f"{esperado}, se encontró {encontrado} ({token.tipo})")

    def intensificador_seguido_de(self, categoria):
        """¿Hay INT y después `categoria`? Es la decisión LL(2) del conflicto 2."""
        return self.ver() == "INT" and self.ver(1) == categoria

    # ------------------------------------------------------------- oración
    def oracion(self):
        hijos = []
        if self.ver() in self.INICIO_SN | {"PRON"}:        # <sujeto_opcional>
            hijos.append(self.sujeto())
        hijos.append(self.predicado())
        hijos.append(self.consumir("PUNTO"))
        if self.ver() != "EOF":
            self.error("se esperaba el fin de la oración")
        return Nodo("oracion", hijos)

    def sujeto(self):
        if self.ver() == "PRON":
            return Nodo("sujeto", [self.consumir("PRON")])
        return Nodo("sujeto", [self.sn()])

    # ---------------------------------------------------- sintagma nominal
    def sn(self):
        if self.ver() == "NPROP":
            return Nodo("sn", [self.consumir("NPROP")])
        if self.ver() == "DET":
            return Nodo("sn", [self.consumir("DET"), self.nominal()])
        self.error("se esperaba un determinante o un nombre propio")

    def nominal(self):
        hijos = self.adjetivos()
        hijos.append(self.consumir("N"))
        hijos += self.adjetivos()
        hijos += self.sps_nominales()
        return Nodo("nominal", hijos)

    def adjetivos(self):
        # Se devuelve una lista de <sadj> en vez de la cadena recursiva
        # <adjetivos> -> <sadj> <adjetivos>, para que el árbol sea más plano.
        lista = []
        while self.ver() == "ADJ" or self.intensificador_seguido_de("ADJ"):
            lista.append(self.sadj())
        return lista

    def sadj(self):
        hijos = [self.consumir("INT")] if self.ver() == "INT" else []
        hijos.append(self.consumir("ADJ"))
        return Nodo("sadj", hijos)

    def sps_nominales(self):
        lista = []
        while self.ver() in self.INICIO_SP:   # regla codiciosa (conflicto 1)
            lista.append(self.sp())
        return lista

    # ---------------------------------------------- sintagma preposicional
    def sp(self):
        if self.ver() == "CONTR":
            return Nodo("sp", [self.consumir("CONTR"), self.nominal()])
        return Nodo("sp", [self.consumir("PREP"), self.sn()])

    # ----------------------------------------------------------- predicado
    def predicado(self):
        hijos = self.adverbios()
        if self.ver() == "NEG":
            hijos.append(self.consumir("NEG"))
        hijos.append(self.sv())
        return Nodo("predicado", hijos)

    def adverbios(self):
        lista = []
        while self.ver() == "ADV" or self.intensificador_seguido_de("ADV"):
            lista.append(self.sadv())
        return lista

    def sadv(self):
        hijos = [self.consumir("INT")] if self.ver() == "INT" else []
        hijos.append(self.consumir("ADV"))
        return Nodo("sadv", hijos)

    def sv(self):
        if self.ver() == "V":
            hijos = [self.consumir("V")]
            if self.ver() in self.INICIO_SN:                # <objeto_opcional>
                hijos.append(Nodo("objeto", [self.sn()]))
        elif self.ver() == "VCOP":
            hijos = [self.consumir("VCOP"), self.atributo()]
        else:
            self.error("se esperaba un verbo")
        hijos += self.circunstanciales()
        return Nodo("sv", hijos)

    def atributo(self):
        if self.ver() in ("ADJ", "INT"):
            return Nodo("atributo", [self.sadj()])
        if self.ver() in self.INICIO_SN:
            return Nodo("atributo", [self.sn()])
        if self.ver() in self.INICIO_SP:
            return Nodo("atributo", [self.sp()])
        self.error("se esperaba un adjetivo, un sintagma nominal o preposicional")

    def circunstanciales(self):
        lista = []
        while True:
            if self.ver() in self.INICIO_SP:
                lista.append(Nodo("circunstancial", [self.sp()]))
            elif self.ver() == "ADV" or self.intensificador_seguido_de("ADV"):
                lista.append(Nodo("circunstancial", [self.sadv()]))
            else:
                return lista


def analizar(texto):
    """Analiza una oración y devuelve su árbol.

    Lanza ErrorLexico o ErrorSintactico si la oración no es válida.
    """
    return Parser(tokenizar(texto)).oracion()


def _oraciones_de_entrada(argv):
    if len(argv) > 1:
        ruta = Path(argv[1])
        if ruta.is_file():
            return [l.strip() for l in ruta.read_text(encoding="utf-8").splitlines()
                    if l.strip() and not l.lstrip().startswith("#")]
        return [" ".join(argv[1:])]
    return ["Juan mira al hombre con el telescopio ."]


if __name__ == "__main__":
    codigo_salida = 0
    for oracion in _oraciones_de_entrada(sys.argv):
        print(f"Oración: {oracion}")
        try:
            arbol = analizar(oracion)
        except ErrorLexico as e:
            print(f"  Error léxico: {e}\n")
            codigo_salida = 1
            continue
        except ErrorSintactico as e:
            print(f"  Error sintáctico: {e}\n")
            codigo_salida = 1
            continue
        print("Sintaxis válida. Árbol sintáctico:")
        print(arbol)
        print()
    sys.exit(codigo_salida)
