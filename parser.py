"""Parser descendente recursivo sencillo para el subconjunto de C++ de TLP02.

Lee tokens de lexer.py; usa funciones para estructuras y una rutina general
para todos los niveles de precedencia de expresiones.
"""
from dataclasses import dataclass, field
from pathlib import Path
from lexer import tokenizar, ErrorLexico


@dataclass
class Nodo:
    nombre: str
    hijos: list = field(default_factory=list)

    def lineas(self, nivel=0):
        yield "  " * nivel + self.nombre
        for hijo in self.hijos:
            if isinstance(hijo, Nodo):
                yield from hijo.lineas(nivel + 1)
            else:
                yield "  " * (nivel + 1) + str(hijo)


class ErrorSintactico(SyntaxError):
    pass


class Parser:
    TIPOS = {"int", "float", "bool"}
    # De menor a mayor precedencia. Sustituye seis funciones casi iguales.
    NIVELES = [
        ("logico_or", "resto_or", {"||"}),
        ("logico_and", "resto_and", {"&&"}),
        ("igualdad", "resto_igualdad", {"==", "!="}),
        ("relacional", "resto_relacional", {"<", ">", "<=", ">="}),
        ("aditivo", "resto_aditivo", {"+", "-"}),
        ("multiplicativo", "resto_multiplicativo", {"*", "/", "%"}),
    ]

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def ver(self, n=0):
        return self.tokens[min(self.pos + n, len(self.tokens)-1)].tipo

    def consumir(self, tipo):
        token = self.tokens[self.pos]
        if token.tipo != tipo:
            raise ErrorSintactico(
                f"Línea {token.linea}, columna {token.columna}: "
                f"se esperaba {tipo!r}, se encontró {token.valor!r}."
            )
        self.pos += 1
        return f"{tipo}({token.valor})" if tipo in ("ID", "NUM") else repr(token.valor)

    def tipo(self):
        if self.ver() not in self.TIPOS:
            self.consumir("int")  # produce un error con ubicación
        return Nodo("<tipo>", [self.consumir(self.ver())])

    def lista(self, elemento, fin, nombre, resto):
        """Analiza listas separadas por comas (parámetros y argumentos)."""
        if self.ver() == fin:
            return Nodo(f"<{nombre}_opcionales>", ["ε"])
        actual = Nodo(f"<{resto}>")
        raiz = Nodo(f"<{nombre}>", [elemento(), actual])
        while self.ver() == ",":
            actual.hijos += [self.consumir(","), elemento()]
            nuevo = Nodo(f"<{resto}>")
            actual.hijos.append(nuevo)
            actual = nuevo
        actual.hijos.append("ε")
        return Nodo(f"<{nombre}_opcionales>", [raiz])

    def parametro(self):
        return Nodo("<parametro>", [self.tipo(), self.consumir("ID")])

    def parametros(self):
        return self.lista(self.parametro, ")", "parametros", "resto_parametros")

    def argumentos(self):
        return self.lista(self.expresion, ")", "argumentos", "resto_argumentos")

    def bloque(self):
        abrir = self.consumir("{")
        sentencias = Nodo("<sentencias>")
        while self.ver() not in ("}", "EOF"):
            sentencias.hijos.append(self.sentencia())
        if not sentencias.hijos:
            sentencias.hijos.append("ε")
        return Nodo("<bloque>", [abrir, sentencias, self.consumir("}")])

    def funcion(self):
        retorno = (Nodo("<tipo_retorno>", [self.consumir("void")])
                   if self.ver() == "void" else Nodo("<tipo_retorno>", [self.tipo()]))
        return Nodo("<funcion>", [retorno, self.consumir("ID"),
            self.consumir("("), self.parametros(), self.consumir(")"), self.bloque()])

    def analizar(self):
        preambulo = Nodo("<preambulo>", [self.consumir(t) for t in
            ("#include", "<", "iostream", ">", "using", "namespace", "std", ";")])
        funciones = Nodo("<funciones>")
        while self.ver() in self.TIPOS | {"void"} and not (
            self.ver() == "int" and self.ver(1) == "main"
        ):
            funciones.hijos.append(self.funcion())
        if not funciones.hijos:
            funciones.hijos.append("ε")
        principal = Nodo("<principal>", [self.consumir(t) for t in ("int", "main", "(", ")")]
                         + [self.bloque()])
        self.consumir("EOF")
        return Nodo("<programa>", [preambulo, funciones, principal])

    def sentencia(self):
        t = self.ver()
        if t == "if":
            hijo = self.condicional()
        elif t == "while":
            hijo = Nodo("<ciclo_while>", [self.consumir("while"), self.consumir("("),
                        self.expresion(), self.consumir(")"), self.sentencia()])
        elif t == "for":
            hijo = Nodo("<ciclo_for>", [self.consumir("for"), self.consumir("("),
                        self.inicio_for(), self.consumir(";"), self.condicion_for(),
                        self.consumir(";"), self.actualizacion_for(), self.consumir(")"),
                        self.sentencia()])
        elif t == "do":
            hijo = Nodo("<ciclo_do>", [self.consumir("do"), self.sentencia(),
                        self.consumir("while"), self.consumir("("), self.expresion(),
                        self.consumir(")"), self.consumir(";")])
        elif t == "switch":
            hijo = self.switch()
        elif t == "{":
            hijo = self.bloque()
        else:
            hijo = self.sentencia_simple()
        return Nodo("<sentencia>", [hijo])

    def condicional(self):
        partes = [self.consumir("if"), self.consumir("("), self.expresion(),
                  self.consumir(")"), self.sentencia()]
        # Dangling else: si viene un 'else', se consume aquí mismo, así que
        # pertenece al 'if' más cercano (la misma regla que usa C++).
        if self.ver() == "else":
            sino = [self.consumir("else"), self.sentencia()]
        else:
            sino = ["ε"]
        return Nodo("<condicional>", partes + [Nodo("<else_opcional>", sino)])

    def sentencia_simple(self):
        if self.ver() in self.TIPOS:
            hijos = [self.tipo(), self.consumir("ID")]
            ini = ([self.consumir("="), self.expresion()] if self.ver() == "=" else ["ε"])
            hijos += [Nodo("<inicializacion>", ini), self.consumir(";")]
            resultado = Nodo("<declaracion>", hijos)
        elif self.ver() == "ID":
            ident = self.consumir("ID")
            if self.ver() == "=":
                continuacion = [self.consumir("="), self.expresion()]
            elif self.ver() == "(":
                continuacion = [self.consumir("("), self.argumentos(), self.consumir(")")]
            elif self.ver() in ("++", "--"):
                continuacion = [self.consumir(self.ver())]
            else:
                self.consumir("=")  # reporta error
            resultado = Nodo("<sentencia_id>", [ident, Nodo("<continuacion_id>", continuacion),
                                                self.consumir(";")])
        elif self.ver() == "break":
            resultado = Nodo("<ruptura>", [self.consumir("break"), self.consumir(";")])
        elif self.ver() == "return":
            palabra = self.consumir("return")
            expr = ["ε"] if self.ver() == ";" else [self.expresion()]
            resultado = Nodo("<retorno>", [palabra, Nodo("<valor_retorno>", expr), self.consumir(";")])
        else:
            token = self.tokens[self.pos]
            raise ErrorSintactico(f"Línea {token.linea}, columna {token.columna}: "
                                  f"se esperaba una sentencia, se encontró {token.valor!r}.")
        return Nodo("<sentencia_simple>", [resultado])

    def switch(self):
        partes = [self.consumir("switch"), self.consumir("("), self.expresion(),
                  self.consumir(")"), self.consumir("{")]
        casos = Nodo("<casos>")
        while self.ver() in ("case", "default"):
            if self.ver() == "case":
                etiqueta = [self.consumir("case")]
                if self.ver() == "-":
                    etiqueta.append(self.consumir("-"))
                etiqueta += [self.consumir("NUM"), self.consumir(":")]
            else:
                etiqueta = [self.consumir("default"), self.consumir(":")]
            sentencias = Nodo("<sentencias>")
            while self.ver() not in ("case", "default", "}", "EOF"):
                sentencias.hijos.append(self.sentencia())
            if not sentencias.hijos:
                sentencias.hijos.append("ε")
            casos.hijos += [Nodo("<etiqueta>", etiqueta), sentencias]
        if not casos.hijos:
            casos.hijos.append("ε")
        return Nodo("<seleccion_switch>", partes + [casos, self.consumir("}")])

    def inicio_for(self):
        if self.ver() == ";":
            return Nodo("<inicio_for>", ["ε"])
        if self.ver() in self.TIPOS:
            hijos = [self.tipo(), self.consumir("ID")]
            ini = [self.consumir("="), self.expresion()] if self.ver() == "=" else ["ε"]
            return Nodo("<inicio_for>", hijos + [Nodo("<inicializacion>", ini)])
        return Nodo("<inicio_for>", [self.consumir("ID"), self.consumir("="), self.expresion()])

    def condicion_for(self):
        return Nodo("<condicion_for>", ["ε"] if self.ver() == ";" else [self.expresion()])

    def actualizacion_for(self):
        if self.ver() == ")":
            return Nodo("<actualizacion_for>", ["ε"])
        ident = self.consumir("ID")
        if self.ver() == "=":
            final = [self.consumir("="), self.expresion()]
        elif self.ver() in ("++", "--"):
            final = [self.consumir(self.ver())]
        else:
            self.consumir("=")  # reporta error
        return Nodo("<actualizacion_for>", [ident, Nodo("<continuacion_actualizacion>", final)])

    def expresion(self):
        return Nodo("<expresion>", [self.nivel(0)])

    def nivel(self, i):
        """Implementa los seis niveles de precedencia con una sola función."""
        if i == len(self.NIVELES):
            return self.unario()
        nombre, resto, operadores = self.NIVELES[i]
        primero = self.nivel(i + 1)
        cola = Nodo(f"<{resto}>")
        raiz = Nodo(f"<{nombre}>", [primero, cola])
        while self.ver() in operadores:
            cola.hijos.extend([self.consumir(self.ver()), self.nivel(i + 1)])
            nueva = Nodo(f"<{resto}>")
            cola.hijos.append(nueva)
            cola = nueva
        cola.hijos.append("ε")
        return raiz

    def unario(self):
        if self.ver() in ("!", "-"):
            return Nodo("<unario>", [self.consumir(self.ver()), self.unario()])
        if self.ver() == "ID":
            ident = self.consumir("ID")
            llamada = ([self.consumir("("), self.argumentos(), self.consumir(")")]
                       if self.ver() == "(" else ["ε"])
            primario = Nodo("<primario>", [ident, Nodo("<llamada_opcional>", llamada)])
        elif self.ver() in ("NUM", "true", "false"):
            primario = Nodo("<primario>", [self.consumir(self.ver())])
        else:
            primario = Nodo("<primario>", [self.consumir("("), self.expresion(), self.consumir(")")])
        return Nodo("<unario>", [primario])


def analizar_codigo(codigo):
    return Parser(tokenizar(codigo)).analizar()


if __name__ == "__main__":
    import sys
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "ejemplos" / "ejemplo.cpp"
    try:
        arbol = analizar_codigo(ruta.read_text(encoding="utf-8"))
        print("Sintaxis válida. Árbol sintáctico:")
        for linea in arbol.lineas():
            print(linea)
    except (SyntaxError, ErrorLexico, OSError) as error:
        print("Error:", error)
        sys.exit(1)
