"""Analizador semántico para el subconjunto de C++ (ver docs/gramatica.bnf).

Verifica reglas SENSIBLES AL CONTEXTO que una gramática libre de contexto
no puede expresar:
  1. Toda variable debe declararse antes de usarse.
  2. No se puede redeclarar una variable en el mismo ámbito.
  3. Los tipos deben ser compatibles en asignaciones y expresiones.
  4. Cada variable solo existe dentro de su ámbito (bloque { }).
  Extra: llamadas a funciones (existencia, número y tipo de argumentos),
  tipo de 'return', existencia de main, 'break' solo dentro de un ciclo o
  switch, y en el switch: expresión int, 'case' enteros sin repetir y un
  solo 'default'.

Trabaja directamente sobre la lista de tokens del lexer, recorriéndola en el
mismo orden que la gramática (descenso recursivo), sin construir un árbol.

Uso:  python semantico.py [archivo.cpp]
"""
from pathlib import Path
import sys
from lexer import tokenizar, ErrorLexico

TIPOS = {"int", "float", "bool"}
NUMERICOS = {"int", "float"}

# Precedencia de operadores binarios (mayor número = se evalúa antes)
PRECEDENCIA = {"||": 1, "&&": 2, "==": 3, "!=": 3,
               "<": 4, ">": 4, "<=": 4, ">=": 4,
               "+": 5, "-": 5, "*": 6, "/": 6, "%": 6}


class ErrorSemantico(Exception):
    pass


class TablaSimbolos:
    """Pila de ámbitos. Cada ámbito es un diccionario {nombre: tipo}.
    Al entrar a un bloque se apila un ámbito nuevo; al salir se desapila."""

    def __init__(self):
        self.ambitos = [{}]
        self.historial = []   # (nombre, tipo, nivel, línea) para mostrar al final

    def abrir(self):
        self.ambitos.append({})

    def cerrar(self):
        self.ambitos.pop()

    def declarar(self, nombre, tipo, linea) -> bool:
        """Devuelve False si el nombre ya existe en el ámbito ACTUAL."""
        if nombre in self.ambitos[-1]:   # -1 = último ámbito de la pila (el actual)
            return False
        self.ambitos[-1][nombre] = tipo
        self.historial.append((nombre, tipo, len(self.ambitos) - 1, linea))
        return True

    def buscar(self, nombre):
        """Busca desde el ámbito más interno hacia afuera. None si no existe."""
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None


def compatible(destino, origen) -> bool:
    """Mismo tipo, o int -> float (promoción). Nada más."""
    return destino == origen or (destino == "float" and origen == "int")


class AnalizadorSemantico:
    def __init__(self, codigo):
        self.tokens = tokenizar(codigo)
        self.pos = 0 # posición del token actual
        self.tabla = TablaSimbolos()
        self.funciones = {}        # nombre -> (tipo_retorno, [tipos de parámetros])
        self.tipo_retorno = None   # tipo de la función que se está analizando
        self.break_valido = 0      # > 0 cuando estamos dentro de un ciclo o switch

    # ---------- utilidades para recorrer los tokens ----------
    def ver(self):
        return self.tokens[self.pos].tipo

    def consumir(self, tipo):
        token = self.tokens[self.pos]
        if token.tipo != tipo:
            self.error(f"se esperaba {tipo!r} y se encontró {token.valor!r}", token)
        self.pos += 1
        return token

    def error(self, mensaje, token):
        raise ErrorSemantico(f"Línea {token.linea}, columna {token.columna}: {mensaje}")

    # ---------- programa y funciones ----------
    def analizar(self):
        if self.ver() == "#include":                      # preámbulo opcional
            for t in ("#include", "<", "iostream", ">", "using", "namespace", "std", ";"):
                self.consumir(t)
        while self.ver() != "EOF":
            self.funcion()
        if "main" not in self.funciones:
            self.error("falta la función main", self.tokens[self.pos])
        return self.tabla.historial

    def funcion(self):
        tipo = self.consumir(self.ver()).valor
        if tipo not in TIPOS | {"void"}:
            self.error(f"se esperaba un tipo de retorno y se encontró {tipo!r}", self.tokens[self.pos - 1])
        nombre = self.consumir("main" if self.ver() == "main" else "ID")
        if nombre.valor in self.funciones:
            self.error(f"función '{nombre.valor}' redeclarada", nombre)

        self.consumir("(")
        parametros = []                                   # lista de (token, tipo)
        while self.ver() != ")":
            if parametros:
                self.consumir(",")
            tipo_param = self.consumir(self.ver()).valor
            if tipo_param not in TIPOS:
                self.error(f"tipo de parámetro inválido {tipo_param!r}", self.tokens[self.pos - 1])
            parametros.append((self.consumir("ID"), tipo_param))
        self.consumir(")")

        # Se registra ANTES del cuerpo para permitir recursión.
        self.funciones[nombre.valor] = (tipo, [t for _, t in parametros])
        self.tipo_retorno = tipo
        self.tabla.abrir()                                # ámbito de la función
        for token, t in parametros:
            if not self.tabla.declarar(token.valor, t, token.linea):
                self.error(f"parámetro '{token.valor}' repetido", token)
        self.bloque(nuevo_ambito=False)                   # el cuerpo comparte ámbito con los parámetros
        self.tabla.cerrar()

    # ---------- sentencias ----------
    def bloque(self, nuevo_ambito=True):
        self.consumir("{")
        if nuevo_ambito:
            self.tabla.abrir()
        while self.ver() not in ("}", "EOF"):
            self.sentencia()
        self.consumir("}")
        if nuevo_ambito:
            self.tabla.cerrar()

    def cuerpo(self):
        """Cuerpo de if/while/for: un bloque o una sola sentencia (con su propio ámbito)."""
        if self.ver() == "{":
            self.bloque()
        else:
            self.tabla.abrir()
            self.sentencia()
            self.tabla.cerrar()

    def cuerpo_ciclo(self):
        """Igual que cuerpo(), pero dentro de él se permite 'break'."""
        self.break_valido += 1
        self.cuerpo()
        self.break_valido -= 1

    def sentencia(self):
        t = self.ver()
        if t == "{":
            self.bloque()
        elif t in TIPOS:
            self.declaracion()
            self.consumir(";")
        elif t == "ID":
            self.sentencia_id()
            self.consumir(";")
        elif t == "if":
            self.consumir("if")
            self.condicion()
            self.cuerpo()
            if self.ver() == "else":
                self.consumir("else")
                self.cuerpo()
        elif t == "while":
            self.consumir("while")
            self.condicion()
            self.cuerpo_ciclo()
        elif t == "do":                       # do cuerpo while (condicion);
            self.consumir("do")
            self.cuerpo_ciclo()
            self.consumir("while")
            self.condicion()
            self.consumir(";")
        elif t == "for":
            self.sentencia_for()
        elif t == "switch":
            self.sentencia_switch()
        elif t == "break":
            token = self.consumir("break")
            if self.break_valido == 0:
                self.error("'break' fuera de un ciclo o switch", token)
            self.consumir(";")
        elif t == "return":
            self.sentencia_return()
        else:
            self.error(f"sentencia no reconocida {self.tokens[self.pos].valor!r}", self.tokens[self.pos])

    def declaracion(self):
        """tipo ID [= expresion]"""
        tipo = self.consumir(self.ver()).valor
        nombre = self.consumir("ID")
        if not self.tabla.declarar(nombre.valor, tipo, nombre.linea):
            self.error(f"la variable '{nombre.valor}' ya fue declarada en este ámbito", nombre)
        if self.ver() == "=":
            self.consumir("=")
            valor = self.expresion()
            if not compatible(tipo, valor):
                self.error(f"no se puede asignar {valor} a '{nombre.valor}' de tipo {tipo}", nombre)

    def sentencia_id(self):
        """ID = expresion  |  ID++  |  ID--  |  ID(argumentos)"""
        nombre = self.consumir("ID")
        if self.ver() == "(":
            self.llamada(nombre)
            return
        tipo = self.tipo_variable(nombre)
        if self.ver() == "=":
            self.consumir("=")
            valor = self.expresion()
            if not compatible(tipo, valor):
                self.error(f"no se puede asignar {valor} a '{nombre.valor}' de tipo {tipo}", nombre)
        elif self.ver() in ("++", "--"):
            if tipo not in NUMERICOS:
                self.error(f"'{self.ver()}' requiere una variable numérica", nombre)
            self.consumir(self.ver())
        else:
            self.error("se esperaba '=', '++', '--' o '('", self.tokens[self.pos])

    def condicion(self):
        inicio = self.consumir("(")
        if self.expresion() != "bool":
            self.error("la condición debe ser de tipo bool", inicio)
        self.consumir(")")

    def sentencia_for(self):
        self.consumir("for")
        self.consumir("(")
        self.tabla.abrir()                    # la variable del for solo existe dentro del for
        if self.ver() in TIPOS:
            self.declaracion()
        elif self.ver() == "ID":
            self.sentencia_id()
        self.consumir(";")
        if self.ver() != ";":
            inicio = self.tokens[self.pos]
            if self.expresion() != "bool":
                self.error("la condición del for debe ser de tipo bool", inicio)
        self.consumir(";")
        if self.ver() != ")":
            self.sentencia_id()
        self.consumir(")")
        self.cuerpo_ciclo()
        self.tabla.cerrar()

    def sentencia_switch(self):
        """switch (expr) { case N: ...  default: ... }"""
        inicio = self.consumir("switch")
        self.consumir("(")
        if self.expresion() != "int":
            self.error("la expresión del switch debe ser de tipo int", inicio)
        self.consumir(")")
        self.consumir("{")
        self.tabla.abrir()
        self.break_valido += 1
        casos_vistos, hay_default = set(), False

        while self.ver() not in ("}", "EOF"):
            if self.ver() == "case":
                token = self.consumir("case")
                signo = -1 if self.ver() == "-" else 1
                if signo == -1:
                    self.consumir("-")
                numero = self.consumir("NUM")
                if "." in numero.valor:
                    self.error("el valor de un 'case' debe ser un entero", numero)
                valor = signo * int(numero.valor)
                if valor in casos_vistos:
                    self.error(f"'case {valor}' repetido", token)
                casos_vistos.add(valor)
                self.consumir(":")
            elif self.ver() == "default":
                token = self.consumir("default")
                if hay_default:
                    self.error("'default' repetido", token)
                hay_default = True
                self.consumir(":")
            elif not casos_vistos and not hay_default:
                self.error("se esperaba 'case' o 'default'", self.tokens[self.pos])
            else:
                self.sentencia()

        self.consumir("}")
        self.break_valido -= 1
        self.tabla.cerrar()

    def sentencia_return(self):
        token = self.consumir("return")
        tipo = "void" if self.ver() == ";" else self.expresion()
        if not compatible(self.tipo_retorno, tipo):
            self.error(f"la función debe retornar {self.tipo_retorno}, no {tipo}", token)
        self.consumir(";")

    # expresiones: cada función devuelve el TIPO de la expresión 
    def expresion(self, minimo=1):
        """Precedencia de operadores: lee un operando y luego, mientras haya un
        operador con prioridad >= minimo, lo combina con el operando derecho."""
        izq = self.unario()
        while self.ver() in PRECEDENCIA and PRECEDENCIA[self.ver()] >= minimo:
            op = self.consumir(self.ver())
            der = self.expresion(PRECEDENCIA[op.valor] + 1)
            izq = self.tipo_binario(op, izq, der)
        return izq

    def tipo_binario(self, op, izq, der):
        o = op.valor
        if o in ("+", "-", "*", "/", "%"):
            if izq not in NUMERICOS or der not in NUMERICOS:
                self.error(f"'{o}' requiere números, se recibió {izq} y {der}", op)
            if o == "%" and (izq, der) != ("int", "int"):
                self.error("'%' requiere dos enteros", op)
            return "float" if "float" in (izq, der) else "int"
        if o in ("<", ">", "<=", ">="):
            if izq not in NUMERICOS or der not in NUMERICOS:
                self.error(f"'{o}' requiere números, se recibió {izq} y {der}", op)
            return "bool"
        if o in ("==", "!="):
            if not (izq == der or {izq, der} <= NUMERICOS):
                self.error(f"no se puede comparar {izq} con {der}", op)
            return "bool"
        # && y ||
        if izq != "bool" or der != "bool":
            self.error(f"'{o}' requiere bool, se recibió {izq} y {der}", op)
        return "bool"

    def unario(self):
        token = self.tokens[self.pos]
        if token.tipo in ("!", "-"):
            self.consumir(token.tipo)
            tipo = self.unario()
            if token.tipo == "!" and tipo != "bool":
                self.error("'!' requiere un bool", token)
            if token.tipo == "-" and tipo not in NUMERICOS:
                self.error("'-' requiere un número", token)
            return tipo
        if token.tipo == "NUM":
            self.consumir("NUM")
            return "float" if "." in token.valor else "int"
        if token.tipo in ("true", "false"):
            self.consumir(token.tipo)
            return "bool"
        if token.tipo == "(":
            self.consumir("(")
            tipo = self.expresion()
            self.consumir(")")
            return tipo
        if token.tipo == "ID":
            self.consumir("ID")
            if self.ver() == "(":
                return self.llamada(token)
            return self.tipo_variable(token)
        self.error(f"se esperaba una expresión y se encontró {token.valor!r}", token)

    def tipo_variable(self, nombre):
        tipo = self.tabla.buscar(nombre.valor)
        if tipo is None:
            self.error(f"la variable '{nombre.valor}' no ha sido declarada", nombre)
        return tipo

    def llamada(self, nombre):
        """Verifica nombre(arg1, arg2, ...) y devuelve el tipo de retorno."""
        if nombre.valor not in self.funciones:
            self.error(f"la función '{nombre.valor}' no ha sido declarada", nombre)
        retorno, parametros = self.funciones[nombre.valor]
        self.consumir("(")
        argumentos = []
        while self.ver() != ")":
            if argumentos:
                self.consumir(",")
            argumentos.append(self.expresion())
        self.consumir(")")
        if len(argumentos) != len(parametros):
            self.error(f"'{nombre.valor}' espera {len(parametros)} argumento(s), "
                       f"se dieron {len(argumentos)}", nombre)
        for i, (esperado, recibido) in enumerate(zip(parametros, argumentos), 1):
            if not compatible(esperado, recibido):
                self.error(f"argumento {i} de '{nombre.valor}': se esperaba {esperado}, "
                           f"se dio {recibido}", nombre)
        return retorno


def analizar_codigo(codigo):
    """Devuelve el historial de la tabla de símbolos o lanza el error encontrado."""
    return AnalizadorSemantico(codigo).analizar()


def imprimir_tabla(historial):
    print(f"  {'NOMBRE':<10} {'TIPO':<6} {'ÁMBITO':<7} LÍNEA")
    for nombre, tipo, nivel, linea in historial:
        print(f"  {nombre:<10} {tipo:<6} {nivel:<7} {linea}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "ejemplos" / "ejemplo.cpp"
    try:
        historial = analizar_codigo(ruta.read_text(encoding="utf-8"))
        print("Análisis semántico correcto. Tabla de símbolos:")
        imprimir_tabla(historial)
    except ErrorLexico as e:
        print("Error léxico:", e)
        sys.exit(1)
    except ErrorSemantico as e:
        print("Error semántico:", e)
        sys.exit(1)
