# Documentación de las pruebas

Los casos están en [`pruebas.py`](../pruebas.py) y se ejecutan con:

```bash
python pruebas.py
```

**Resultado actual: 25/25 casos correctos.**

| Grupo | Cantidad |
|---|---|
| Programas válidos | 6 |
| Errores léxicos | 4 |
| Errores semánticos | 15 |
| **Total** | **25** |

## Cómo funcionan

Cada caso es una tupla `(esperado, título, código)`:

- `esperado` es el resultado que debe dar el análisis: `"ok"`, `"lexico"` o `"semantico"`.
- Cada código se pasa por `analizar_codigo()` de `semantico.py`, que primero llama al lexer y luego hace el análisis semántico.
- Un caso **PASA** si el tipo de resultado obtenido coincide con el esperado.

Casi todos los casos usan la función `programa(cuerpo, extra)`, que genera este código:

```cpp
<extra>                // línea 1 (vacía si no hay extra)
int main() {           // línea 2
<cuerpo>               // el cuerpo empieza en la línea 3
    return 0;
}
```

Por eso, en los mensajes de error, la **línea 3** es la primera línea del cuerpo.

---

## 1. Programas válidos

Deben pasar el lexer y el analizador semántico sin errores.

### V1 · Declaraciones y expresiones
```cpp
int a = 5;
float b = a * 2.5;
bool c = a > 3 && !(b == 1.0);
```
**Qué prueba:**
- `int * float` da `float`, que se puede asignar a `float`;
- una comparación da `bool`;
- `&&` y `!` reciben `bool`;
- `==` entre `float` y un literal real.

**Resultado:** sin errores.

### V2 · Ámbitos: la misma variable en bloques distintos
```cpp
{ int x = 1; }
{ float x = 2.0; }
```
**Qué prueba:** al cerrar el primer bloque, `x` se elimina de la tabla de símbolos, así que se puede volver a declarar en otro bloque, incluso con otro tipo.

**Resultado:** sin errores.

### V3 · Sombreado
```cpp
int x = 1;
{ bool x = true; }
x = x + 1;
```
**Qué prueba:**
- declarar `x` dentro de un bloque interno **no** es una redeclaración, porque es otro ámbito;
- al salir del bloque, `x` vuelve a ser la variable `int` externa, así que `x + 1` es válido.

**Resultado:** sin errores.

### V4 · `for`, `while`, `if`/`else` y una función
```cpp
int doble(int n) { return n * 2; }
...
int t = 0;
for (int i = 0; i < 3; i++) { t = t + doble(i); }
while (t > 0) t--;
if (t == 0) t = 1; else t = 2;
```
**Qué prueba:**
- la función se declara y luego se llama con un argumento de tipo correcto;
- `return` devuelve un `int` en una función `int`;
- las condiciones son `bool`;
- `while`, `if` y `else` aceptan cuerpos sin llaves.

**Resultado:** sin errores.

### V5 · `do-while` con `break`
```cpp
int n = 10;
do {
    n--;
    if (n == 5) break;
} while (n > 0);
```
**Qué prueba:**
- el `break` está dentro del `do-while`, aunque esté anidado en un `if`;
- la condición del `do-while` es `bool`.

**Resultado:** sin errores.

### V6 · `switch` con `case`, `default` y `break`
```cpp
int op = 2;
int r = 0;
switch (op) {
    case 1: r = 10; break;
    case -1: r = -10; break;
    default: r = 0;
}
```
**Qué prueba:**
- la expresión del `switch` es `int`;
- los `case` son enteros distintos (incluye uno negativo);
- hay un solo `default`;
- `break` es válido dentro del `switch`.

**Resultado:** sin errores.

---

## 2. Errores léxicos

Los detecta `lexer.py` antes de que empiece el análisis semántico.

| # | Caso | Código | Mensaje esperado |
|---|---|---|---|
| L1 | Carácter no válido | `int a = 3 @ 4;` | `Línea 3, columna 15: carácter no válido '@'` |
| L2 | Número mal formado (dígito seguido de letras) | `int a = 12abc;` | `Línea 3, columna 13: número mal formado '12abc'` |
| L3 | Número mal formado (dos puntos decimales) | `float a = 1.2.3;` | `Línea 3, columna 15: número mal formado '1.2.3'` |
| L4 | Comentario de bloque sin cerrar | `int a = 1; /* nunca se cierra` | `Línea 3, columna 16: comentario sin cerrar` |

**Por qué son errores léxicos:**

- **L1:** `@` no encaja con ninguna expresión regular de token, así que cae en la regla `ERROR`.
- **L2 y L3:** el lexer toma todo lo que empieza con un dígito (`\d[\w.]*`) y luego verifica que coincida completo con `\d+(\.\d+)?`. Si no coincide, es un literal mal formado. Sin esta validación, `12abc` se partiría en `12` + `abc` y el error se reportaría más tarde con un mensaje confuso.
- **L4:** el comentario de bloque necesita su cierre `*/`. Si no existe, se activa la regla `COMENTARIO_MAL`.

---

## 3. Errores semánticos

El código es léxicamente válido, pero viola una regla que depende del contexto.

### Declaraciones y ámbitos

| # | Caso | Código | Mensaje esperado |
|---|---|---|---|
| S1 | Variable no declarada | `total = 5;` | `Línea 3, columna 5: la variable 'total' no ha sido declarada` |
| S2 | Redeclaración en el mismo ámbito | `int x = 1;`<br>`int x = 2;` | `Línea 4, columna 9: la variable 'x' ya fue declarada en este ámbito` |
| S5 | Variable usada fuera de su ámbito | `{ int x = 2; }`<br>`x = 3;` | `Línea 4, columna 5: la variable 'x' no ha sido declarada` |
| S6 | Variable del `for` usada afuera | `for (int i = 0; i < 3; i++) { }`<br>`i = 5;` | `Línea 4, columna 5: la variable 'i' no ha sido declarada` |

**Qué demuestran:**

- **S1:** `buscar()` recorre toda la pila de ámbitos y no encuentra `total`.
- **S2:** `declarar()` encuentra `x` en el ámbito actual (el tope de la pila).
- **S5 y S6:** la variable sí se declaró, pero su ámbito ya se cerró. En S6, el `for` abre su propio ámbito para `i`.
- **Comparar con V2 y V3:** el mismo nombre en ámbitos *distintos* es válido.

### Tipos

| # | Caso | Código | Mensaje esperado |
|---|---|---|---|
| S3 | Asignar `int` a `bool` | `bool activo = 4;` | `Línea 3, columna 10: no se puede asignar int a 'activo' de tipo bool` |
| S4 | Asignar `float` a `int` | `int n = 2.5;` | `Línea 3, columna 9: no se puede asignar float a 'n' de tipo int` |
| S7 | Suma entre `int` y `bool` | `int a = 1 + true;` | `Línea 3, columna 15: '+' requiere números, se recibió int y bool` |
| S8 | Condición no booleana en `if` | `int a = 1;`<br>`if (a) a = 2;` | `Línea 4, columna 8: la condición debe ser de tipo bool` |

**Qué demuestran:**

- **S3 y S4:** la función `compatible()` solo permite tipos iguales o la promoción `int` → `float`. Por eso `float` → `int` (S4) se rechaza: se perdería la parte decimal.
- **S7:** `tipo_binario()` exige que los operadores aritméticos reciban números.
- **S8:** en este subconjunto, a diferencia de C++ real, las condiciones deben ser `bool`.

### Funciones

| # | Caso | Código | Mensaje esperado |
|---|---|---|---|
| S9 | Faltan argumentos en la llamada | `int suma(int a, int b) {...}`<br>`int r = suma(1);` | `Línea 3, columna 13: 'suma' espera 2 argumento(s), se dieron 1` |
| S10 | `return` de tipo incorrecto | `bool f() { return 3; }` | `Línea 1, columna 12: la función debe retornar bool, no int` |

**Qué demuestran:**

- **S9:** la firma de cada función se guarda en `self.funciones` (tipo de retorno y tipos de los parámetros) y se compara con cada llamada.
- **S10:** mientras se analiza el cuerpo de una función, `self.tipo_retorno` guarda su tipo, y cada `return` se compara contra él.

### `do-while`, `switch` y `break`

| # | Caso | Código | Mensaje esperado |
|---|---|---|---|
| S11 | `break` fuera de un ciclo o `switch` | `int a = 1;`<br>`break;` | `Línea 4, columna 5: 'break' fuera de un ciclo o switch` |
| S12 | Condición del `do-while` no booleana | `int n = 3;`<br>`do { n--; } while (n);` | `Línea 4, columna 23: la condición debe ser de tipo bool` |
| S13 | `switch` sobre un `float` | `float f = 1.5;`<br>`switch (f) { case 1: break; }` | `Línea 4, columna 5: la expresión del switch debe ser de tipo int` |
| S14 | `case` repetido | `switch (op) { case 1: break; case 1: break; }` | `Línea 4, columna 34: 'case 1' repetido` |
| S15 | `default` repetido | `switch (op) { default: break; default: break; }` | `Línea 4, columna 35: 'default' repetido` |

**Qué demuestran:**

- **S11:** el contador `break_valido` vale 0 fuera de ciclos y `switch`. La gramática sí permite `break;` en cualquier lugar, así que es el semántico el que lo rechaza.
- **S12:** el `do-while` aplica la misma regla de condición `bool` que `if` y `while`.
- **S13:** el `switch` solo acepta expresiones enteras.
- **S14 y S15:** los valores de `case` ya vistos se guardan en un `set`, y se lleva una bandera para saber si ya hubo un `default`.

---

## Relación con la jerarquía de Chomsky

| Grupo | Lo detecta | Por qué ahí |
|---|---|---|
| Errores léxicos (L1–L4) | `lexer.py` | Basta un autómata finito (expresiones regulares) para saber si un fragmento es un token válido. |
| Errores semánticos (S1–S15) | `semantico.py` | La estructura de todos estos programas es **sintácticamente correcta**: la CFG los aceptaría si se les agrega el preámbulo `#include`, que el semántico trata como opcional para que los casos sean más cortos. Rechazarlos exige recordar información de otras partes del programa (nombres declarados, tipos, firmas, contexto de ciclo, valores de `case` ya vistos). Esa memoria no la tiene una CFG; la aporta la tabla de símbolos. |
