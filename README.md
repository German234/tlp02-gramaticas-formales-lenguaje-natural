# Proyecto TLP02-2026 — Fase 1: Lexer y analizador semántico

Este proyecto implementa un analizador léxico (lexer) y un analizador semántico para un **subconjunto de C++**, escritos en Python. También incluye un parser descendente recursivo que construye el árbol sintáctico.

| Fase del compilador | Archivo | Jerarquía de Chomsky |
|---|---|---|
| Análisis léxico | `lexer.py` | Lenguaje regular (tipo 3) |
| Análisis sintáctico | `parser.py` | Lenguaje libre de contexto (tipo 2) |
| Análisis semántico | `semantico.py` | Reglas sensibles al contexto (tipo 1) |

## Requisitos

- Python 3.9 o superior.
- No se necesitan librerías externas: solo se usa la biblioteca estándar.

## Estructura del proyecto

```
cpp_parser/
├── lexer.py            # Analizador léxico: código fuente -> lista de tokens
├── parser.py           # Analizador sintáctico: tokens -> árbol sintáctico
├── semantico.py        # Analizador semántico: tabla de símbolos, tipos y ámbitos
├── pruebas.py          # Casos de prueba (válidos y con errores)
├── ejemplos/
│   ├── ejemplo.cpp          # Programa válido que usa todo el subconjunto
│   ├── error_lexico.cpp     # Programa con un error léxico (para la demo)
│   └── error_semantico.cpp  # Programa con un error semántico (para la demo)
└── docs/
    ├── gramatica.bnf   # Gramática libre de contexto del subconjunto
    └── PRUEBAS.md      # Documentación de cada caso de prueba
```

## Subconjunto de C++ soportado

- **Tipos:** `int`, `float`, `bool` y `void` (`void` solo como tipo de retorno de una función).
- **Sentencias:**
  - declaraciones con inicialización opcional;
  - asignación, `++` y `--`;
  - llamadas a funciones;
  - `if` / `else`, `while`, `do-while` y `for`, con o sin llaves (el dangling else se explica más abajo);
  - `switch` con `case`, `default` y `break`;
  - `return`;
  - bloques `{ }`.
- **Expresiones:**
  - aritméticas: `+ - * / %`;
  - relacionales: `< > <= >=`;
  - de igualdad: `== !=`;
  - lógicas: `&& || !`;
  - menos unario `-` y paréntesis.
- **Estructura de un programa:**
  - preámbulo opcional `#include <iostream>` y `using namespace std;`;
  - funciones;
  - `int main()`.

### Especificación de tokens

Los tokens se definen con expresiones regulares en `lexer.py` (lista `ESPECIFICACION`):

| Token | Expresión regular | Ejemplos |
|---|---|---|
| Comentario (se descarta) | `//[^\n]*` o `/\*[\s\S]*?\*/` | `// nota`, `/* bloque */` |
| Espacio (se descarta) | `\s+` | espacios, tabs, saltos de línea |
| `#include` | `\#include\b` | `#include` |
| Número | `\d+(\.\d+)?` | `42`, `3.14` |
| Identificador | `[A-Za-z_]\w*` | `total`, `_x1` |
| Palabra reservada | Un identificador que está en `PALABRAS_RESERVADAS` | `int`, `while`, `switch` |
| Operador | `== != <= >= && \|\| ++ -- + - * / % < > = !` | `<=`, `&&` |
| Delimitador | `( ) { } ; , :` | `{`, `;` |

**Palabras reservadas:** `using namespace std iostream main int float bool void if else while do for return switch case default break true false`

**Errores léxicos detectados:**

| Error | Ejemplo |
|---|---|
| Carácter no válido | `@`, `$`, `&` solo |
| Número mal formado | `12abc`, `3.`, `1.2.3` |
| Comentario de bloque sin cerrar | `/* ...` |

### Dangling else

La regla `<condicional> ::= 'if' '(' <expresion> ')' <sentencia> <else_opcional>` es **ambigua**. En

```cpp
if (a) if (b) x = 1; else x = 2;
```

el `else` podría pertenecer a cualquiera de los dos `if`. En términos LL(1), el conflicto está en que `'else'` pertenece a FIRST(`<else_opcional>`) y también a FOLLOW(`<else_opcional>`).

Se resuelve **como en C++**: el estándar (`[stmt.if]`) añade la regla *"el `else` se asocia con el `if` más cercano que no tenga `else`"*. El parser la aplica consumiendo el `else` apenas lo ve ("else codicioso"), igual que hacen GCC y Clang. Un parser LR, como uno generado con Bison, obtiene lo mismo resolviendo el conflicto *shift/reduce* a favor de *shift*.

La alternativa teórica es reescribir la gramática con sentencias **emparejadas** (todo `if` tiene su `else`) y **abiertas**. Así se elimina la ambigüedad dentro de la propia gramática, a cambio de duplicar las reglas de `if`, `while` y `for`:

```
<sentencia>  ::= <emparejada> | <abierta>
<emparejada> ::= 'if' '(' E ')' <emparejada> 'else' <emparejada> | ... | <sentencia_simple>
<abierta>    ::= 'if' '(' E ')' <sentencia>
               | 'if' '(' E ')' <emparejada> 'else' <abierta> | ...
```

Elegimos la versión estilo C++ porque es más corta, coincide con el código del parser y es la que usan los compiladores reales.

## Cómo usar cada archivo

Todos los comandos se ejecutan desde la carpeta `cpp_parser/`. Si no se indica un archivo, cada script analiza `ejemplos/ejemplo.cpp`.

### 1. Lexer: ver los tokens

```bash
python lexer.py                       # analiza ejemplos/ejemplo.cpp
python lexer.py mi_programa.cpp       # analiza otro archivo
```

Salida: un token por línea, con su posición, su tipo y su lexema.

```
LÍN:COL  TIPO       LEXEMA
  9:1    int        'int'
  9:5    ID         'sumar'
  9:10   (          '('
```

Si encuentra un error, muestra su línea y columna y termina con código 1:

```
Error léxico: Línea 3, columna 13: número mal formado '12abc'
```

### 2. Parser: ver el árbol sintáctico

```bash
python parser.py
python parser.py mi_programa.cpp
```

El parser exige el preámbulo (`#include <iostream>` y `using namespace std;`), y `int main()` debe ser la última función.

### 3. Analizador semántico: verificar el programa

```bash
python semantico.py
python semantico.py mi_programa.cpp
```

Si el programa es correcto, muestra la **tabla de símbolos**: cada variable declarada, su tipo, su nivel de ámbito (1 = parámetros y cuerpo de la función, 2 o más = bloques internos como `for`, `if` o `{ }`) y su línea.

```
Análisis semántico correcto. Tabla de símbolos:
  NOMBRE     TIPO   ÁMBITO  LÍNEA
  a          int    1       9
  b          int    1       9
  ...
  total      int    1       39
  contador   int    1       40
  precio     float  1       41
  listo      bool   1       42
  descuento  float  1       45
  rango      bool   1       46
  i          int    2       49
  opcion     int    1       72
  total      bool   2       86
```

Esta tabla es un historial: muestra cada declaración en el orden en que ocurrió, incluidas las de variables cuyo ámbito ya se cerró. Por eso `total` aparece dos veces, con niveles de ámbito distintos.

Si encuentra un error, indica de qué tipo es (léxico o semántico), su ubicación y la causa:

```
Error semántico: Línea 4, columna 9: la variable 'x' ya fue declarada en este ámbito
```

El analizador semántico llama primero al lexer, así que también reporta los errores léxicos.

### Usarlos desde otro script de Python

```python
from lexer import tokenizar, ErrorLexico
from semantico import analizar_codigo, ErrorSemantico

tokens = tokenizar("int main() { int x = 1; return 0; }")
historial = analizar_codigo("int main() { int x = 1; return 0; }")
```

## Cómo ejecutar las pruebas

```bash
python pruebas.py
```

El script ejecuta **25 casos**:

- 6 válidos;
- 4 con errores léxicos;
- 15 con errores semánticos.

Para cada caso muestra si pasa o falla y el mensaje obtenido. Al final imprime el total:

```
[PASA] Variable no declarada
        -> Error semántico: Línea 3, columna 5: la variable 'total' no ha sido declarada
...
25/25 casos correctos
```

Un caso **PASA** cuando el resultado obtenido (`ok`, `lexico` o `semantico`) coincide con el esperado.

### Agregar una prueba nueva

Agregue una tupla a la lista `CASOS` en `pruebas.py`:

```python
("semantico", "Descripción del caso", programa("    int a = true;")),
```

- El primer valor es el resultado esperado: `"ok"`, `"lexico"` o `"semantico"`.
- La función `programa(cuerpo, extra="")` envuelve las líneas dentro de `int main() { ... return 0; }`. En `extra` se pueden poner funciones que van antes de `main`.
- Los casos que no siguen esa forma (por ejemplo, una función con un `return` incorrecto) se escriben como una cadena con el programa completo.

La descripción de cada caso de prueba está en [docs/PRUEBAS.md](docs/PRUEBAS.md).

## Reglas que verifica el analizador semántico

Usa una **tabla de símbolos** implementada como una pila de ámbitos (clase `TablaSimbolos`):

- al entrar a un bloque `{ }`, a una función, a un `for` o a un `switch`, se apila un diccionario nuevo;
- al salir, se desapila;
- para buscar una variable, se recorre la pila desde el ámbito más interno hacia afuera.

| Regla | Ejemplo que la viola |
|---|---|
| Toda variable se declara antes de usarse | `total = 5;` sin declarar `total` |
| No hay redeclaraciones en el mismo ámbito | `int x = 1; int x = 2;` |
| Una variable solo existe dentro de su ámbito | `{ int x; } x = 3;` |
| Asignaciones compatibles (se permite `int` → `float`) | `bool b = 4;`, `int n = 2.5;` |
| Operandos compatibles en las expresiones | `1 + true`, `!5` |
| Las condiciones de `if`, `while`, `do-while` y `for` son `bool` | `if (a)` con `a` de tipo `int` |
| Llamadas con la cantidad y el tipo de argumentos correctos | `suma(1)` cuando `suma` recibe 2 |
| `return` del mismo tipo que la función | `bool f() { return 3; }` |
| `break` solo dentro de un ciclo o un `switch` | `break;` suelto en `main` |
| `switch` sobre un `int`, sin `case` repetidos y con un solo `default` | `case 1: ... case 1:` |
| Debe existir la función `main` | un programa sin `main` |

## Reflexión: ¿qué verificaciones no puede expresar una CFG?

Una gramática libre de contexto decide si una cadena es válida aplicando producciones de la forma `A → α`. Cada no terminal se reemplaza **sin importar lo que lo rodea**. Además, un autómata de pila no puede "recordar" un conjunto arbitrario de nombres para consultarlo más adelante. Por eso estas reglas quedan fuera de la CFG y se verifican en la fase semántica:

- **"Toda variable usada debe estar declarada".** Es el ejemplo clásico. Equivale al lenguaje `{ w c w | w ∈ {a,b}* }`: una cadena (el nombre declarado) debe reaparecer idéntica más adelante (el uso). Con el lema de bombeo para lenguajes libres de contexto se demuestra que ese lenguaje **no es libre de contexto**, y sí es sensible al contexto. La gramática solo puede decir "aquí va un `ID`". No puede exigir que ese `ID` sea uno que apareció antes.
- **Redeclaraciones y ámbitos.** Para saber si `x` ya existe en el bloque actual hay que comparar contra todos los nombres declarados en él. Es la misma dependencia de "copiar y comparar" del punto anterior.
- **Compatibilidad de tipos.** La producción `<declaracion> ::= <tipo> ID '=' <expresion>` acepta tanto `int x = 5` como `bool x = 5`. Para rechazar la segunda hay que propagar información (el tipo) entre partes distantes del árbol. Eso lo hace un analizador con atributos, no una CFG pura.
- **Número y tipo de argumentos en una llamada.** Hay que relacionar la definición de la función con cada uno de sus usos, que pueden estar en cualquier parte del programa.
- **`break` dentro de un ciclo y `case` sin repetir.** Dependen del contexto en el que aparece la sentencia o de valores vistos antes. La gramática genera `break;` como una sentencia más, en cualquier lugar.

En resumen:

- el **lexer** trabaja con lenguajes regulares (un autómata finito basta para reconocer cada token);
- el **parser** trabaja con lenguajes libres de contexto (la estructura anidada se reconoce con una pila);
- el **analizador semántico** cubre las dependencias sensibles al contexto, usando una tabla de símbolos que funciona como la "memoria" que le falta a la CFG.
