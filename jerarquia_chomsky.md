# Jerarquía de Chomsky y limitaciones de las CFG en el proyecto

## 1. La jerarquía de Chomsky en el proyecto

En el proyecto se aplican distintos niveles de la jerarquía de Chomsky para construir las etapas de análisis del lenguaje, cada nivel permite reconocer un tipo diferente de estructura y tiene capacidades y limitaciones específicas.

En la jerarquía de Chomsky se puede clasificar las gramáticas formales en cuatro tipos, en nuestro proyecto se utilizan principalmente los lenguajes regulares (tipo 3) y las gramáticas libres de contexto (tipo 2). Además, para realizar ciertas comprobaciones semánticas es necesario
utilizar información contextual que no puede obtenerse únicamente mediante estas gramáticas.

---

## 2. Tipo 3 — Los lenguajes regulares

El analizador léxico (`lexer.py`) utiliza patrones definidos mediante expresiones regulares para reconocer los elementos individuales del código fuente; es por esta razón que se relaciona con las gramáticas de tipo 3 de la jerarquía de Chomsky, también conocidas como gramáticas regulares.

Es en esta etapa que se identifican los tokens que componen el programa, por ejemplo:

-   Palabras reservadas: `int`, `float`, `bool`, `if`, `while` y
    `return`.
-   Identificadores: `edad`, `resultado` o `calcular`.
-   Números: `10` o `3.14`.
-   Operadores: `+`, `-`, `=`, `==` y `&&`.
-   Signos de puntuación y delimitadores: `;`, `,`, `(`, `)` y `{`, `}`.

---

Por ejemplo, al analizar la instrucción:

``` cpp
int edad = 20;
```

el lexer reconoce los elementos que la forman: la palabra reservada `int`, el identificador `edad`, el operador `=`, el número `20` y el punto y coma `;`. También registra información como el tipo de token, el lexema, la línea y la columna donde aparece.

Es por ello que las expresiones regulares son adecuadas para reconocer estos patrones individuales, sin embargo, el lexer no determina por sí solo si la instrucción tiene sentido dentro del programa. Por ejemplo, puede reconocer correctamente el identificador `edad`, pero no sabe si esa variable fue declarada anteriormente o si está disponible en el ámbito donde se utiliza.

## 3. Tipo 2 — Las CFG 

En el analizador sintáctico (`parser.py`) se utiliza las reglas de una gramática libre de contexto (CFG), correspondientes al tipo 2 de la
jerarquía de Chomsky. Estas gramáticas permiten describir cómo se combinan los tokens para formar estructuras válidas del lenguaje.

En el proyecto, la gramática BNF (`docs/gramatica.bnf`) se definen estructuras como:

-   Declaraciones de variables.
-   Declaraciones y llamadas a funciones.
-   Asignaciones.
-   Expresiones aritméticas y lógicas.
-   Condicionales (`if` y `else`).
-   Ciclos (`while`, `for` y `do-while`).
-   Sentencias de retorno (`return`).
-   Bloques delimitados por llaves.

Por ejemplo, una regla de la gramática establece que una declaración está formada por un tipo, un identificador, una inicialización opcional y un punto y coma:

``` bnf
<declaracion> ::= <tipo> ID <inicializacion> ';'
```

Esta regla permite reconocer la estructura de una instrucción como:

``` cpp
int edad = 20;
```

También permite detectar que una instrucción no respeta la estructura esperada, por ejemplo, si falta el punto y coma:

``` cpp
int edad = 20
```

Es por ello que, las CFG permiten describir la organización sintáctica del programa y comprobar que los tokens aparecen en un orden permitido por las reglas de la gramática.

---

## 4. Las limitaciones de una CFG

Las gramáticas libres de contexto permiten describir estructuras sintácticas de manera recursiva, pero aun así no son suficientes para comprobar todas las condiciones que debe cumplir un programa. En particular, una CFG no mantiene por sí sola información sobre las declaraciones anteriores, los tipos de las variables, los ámbitos en los que están disponibles o la relación entre los argumentos y los parámetros de una función.

Esto significa que una instrucción puede estar correctamente construida desde el punto de vista sintáctico, pero aun así contener un error
semántico.

A continuación, se presentan algunas limitaciones relevantes para el proyecto.

### 4.1. No comprobar si una variable fue declarada antes de utilizarse

Una CFG puede reconocer la estructura de una asignación o de una expresión que contiene un identificador, pero no puede comprobar por si
sola si ese identificador fue declarado anteriormente.

Por ejemplo:

``` cpp
int main() {
    edad = 20;
    return 0;
}
```

La asignación tiene una estructura sintáctica válida: contiene un identificador, un operador de asignación, una expresión y un punto y coma;sin embargo, la variable `edad` no fue declarada previamente.

Para detectar este error se necesita consultar la información de las declaraciones realizadas durante el análisis del programa.

### 4.2. No detectar por sí sola las redeclaraciones en un mismo ámbito

Una CFG puede reconocer dos declaraciones con la misma estructura, pero no conserva automáticamente un registro que permita comparar los nombres declarados anteriormente.

Por ejemplo:

``` cpp
int main() {
    int edad = 20;
    int edad = 25;
    return 0;
}
```

Las dos declaraciones cumplen con la estructura sintáctica de una declaración de variable. No obstante, el programa presenta una
redeclaración de `edad` dentro del mismo ámbito.

Para identificar este problema es necesario registrar los identificadores declarados en cada ámbito y comprobar si el nombre ya existe en el ámbito actual.

### 4.3. No verificar si los tipos de datos son compatibles en una asignación

La gramática puede reconocer una asignación sin determinar necesariamente si el tipo de la variable es compatible con el tipo del valor asignado.

Por ejemplo:

``` cpp
int edad = true;
```

La instrucción puede cumplir con la estructura sintáctica de una declaración con inicialización. Sin embargo, existe una incompatibilidad entre el tipo `int` de la variable y el tipo `bool` del valor asignado.

Para detectar este error, el análisis semántico debe conocer el tipo declarado de la variable y el tipo de la expresión que se le asigna.

### 4.4. No determinar si una variable está disponible dentro del ámbito donde se utiliza

Las CFG pueden describir bloques delimitados por llaves, pero no administran por sí solas la visibilidad de las variables declaradas dentro de esos bloques.

Por ejemplo:

``` cpp
int main() {
    {
        int temporal = 10;
    }

    temporal = 20;
    return 0;
}
```

La variable `temporal` fue declarada dentro de un bloque interno, cuando ese bloque termina, la variable deja de estar disponible fuera de él.
Por ello, la asignación posterior debe producir un error semántico.

Para realizar esta comprobación se necesita llevar un control de los ámbitos y de las variables que pertenecen a cada uno.

### 4.5. No comprobar por sí sola la correspondencia entre argumentos y parámetros de una función

Una CFG puede reconocer la estructura de una declaración o llamada a función y permitir listas de parámetros y argumentos. Sin embargo, no comprueba por sí sola que la cantidad y los tipos de los argumentos coincidan con los parámetros definidos para esa función.

Por ejemplo:

``` cpp
int sumar(int a, int b) {
    return a + b;
}

int main() {
    int resultado = sumar(5);
    return 0;
}
```

La llamada `sumar(5)` tiene una estructura sintáctica válida, pero la función requiere dos argumentos y solamente recibe uno.

También podría existir una llamada con una cantidad correcta de argumentos, pero con tipos incompatibles. Por ejemplo, si una función espera un parámetro de tipo `bool` y recibe un valor de tipo `float`, el análisis semántico debe comprobar si esa combinación está permitida.

Para detectar estos errores se necesita almacenar la información de las funciones, incluyendo su tipo de retorno y los tipos de sus parámetros, y compararla con los argumentos de cada llamada.


---

## 5. La solución: tabla de símbolos

Para superar estas limitaciones, el proyecto incorpora un analizador semántico (`semantico.py`) que utiliza una tabla de símbolos. Esta estructura almacena información sobre los identificadores declarados y permite consultar esa información durante el análisis del programa.

```python
class TablaSimbolos:
    """Pila de ámbitos. Cada ámbito es un diccionario {nombre: tipo}.
    Al entrar a un bloque se apila un ámbito nuevo; al salir se desapila."""

    def __init__(self):
        self.ambitos = [{}]
        self.historial = []   # (nombre, tipo, nivel, línea) para mostrar al final

    def abrir(self):
        self.ambitos.append({})  # al entrar a un bloque

    def cerrar(self):
        self.ambitos.pop()  # al salir del bloque

    def declarar(self, nombre, tipo, linea) -> bool:
        """Devuelve False si el nombre ya existe en el ámbito ACTUAL."""
        if nombre in self.ambitos[-1]:             # ya existe en el ámbito ACTUAL
            return False
        self.ambitos[-1][nombre] = tipo
        self.historial.append((nombre, tipo, len(self.ambitos) - 1, linea))
        return True

    def buscar(self, nombre):               # del ámbito más interno hacia afuera
        """Busca desde el ámbito más interno hacia afuera. None si no existe."""
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

```
La tabla de símbolos mantiene los nombres de las variables y sus tipos, organizados por ámbitos. En la implementación del proyecto, los ámbitos se administran mediante una pila de diccionarios: al entrar en un nuevo bloque se crea un ámbito y, al salir de él, se elimina. Cuando se busca una variable, se revisan los ámbitos desde el más interno hacia los externos.

Gracias a este mecanismo, el analizador semántico puede realizar comprobaciones que no se resuelven únicamente con las reglas de una CFG:

1.  **Declaración previa:** verifica que una variable exista en la tabla de símbolos antes de utilizarla.
2.  **Redeclaración:** comprueba que una variable no se declare dos veces dentro del mismo ámbito.
3.  **Compatibilidad de tipos:** consulta los tipos registrados y verifica si son compatibles en asignaciones y expresiones.
4.  **Control de ámbitos:** determina si una variable continúa disponible en el lugar donde se utiliza.
5.  **Verificación de funciones:** almacena el tipo de retorno y los tipos de los parámetros para comprobar las llamadas y sus argumentos.

Por ejemplo, al procesar:

``` cpp
int main() {
    int edad = 20;
    edad = 25;
    return 0;
}
```

el analizador registra `edad` como una variable de tipo `int`. Cuando encuentra la asignación posterior, consulta la tabla de símbolos, recupera su tipo y comprueba que el valor asignado sea compatible.

En cambio, si encuentra:

``` cpp
int main() {
    edad = 25;
    return 0;
}
```

consulta la tabla y detecta que `edad` no ha sido declarada, por lo que genera un error semántico.

Es importante distinguir las responsabilidades de cada etapa: el parser utiliza la gramática libre de contexto para comprobar la estructura del programa; el analizador semántico utiliza la información obtenida y la tabla de símbolos para verificar condiciones que dependen del contexto.
Por ello, no se debe considerar que la tabla de símbolos sea una CFG, sino un mecanismo complementario para realizar el análisis semántico.

---

## 6. Relación entre la jerarquía de Chomsky y los componentes del proyecto

| Tipo | Archivo | Aplicación en este proyecto |
|---|---|---|
| **Tipo 3: lenguajes regulares** | `lexer.py` | El lexer reconoce patrones mediante expresiones regulares: identificadores, números, operadores, delimitadores y palabras reservadas. |
| **Tipo 2: gramáticas libres de contexto** | `docs/gramatica.bnf`, `parser.py` | Describen la estructura de declaraciones, sentencias y expresiones del subconjunto de C++. |
| **Comprobaciones sensibles al contexto** | `semantico.py` | Verifican declaración previa, tipos y ámbitos mediante una tabla de símbolos. |

La idea central es que **cada nivel resuelve lo que el anterior no puede.**

---

## 7. Conclusión

La implementación del proyecto permite observar que cada nivel de análisis cumple una función diferente. Los lenguajes regulares del tipo 3 facilitan el reconocimiento de los elementos individuales del código, mientras que las gramáticas libres de contexto del tipo 2 permiten describir cómo esos elementos se organizan para formar instrucciones y estructuras más complejas.

Sin embargo, reconocer que un programa cumple con las reglas sintácticas no garantiza que sea semánticamente correcto. Una variable puede utilizarse sin haber sido declarada, una asignación puede contener tipos incompatibles o una llamada puede enviar argumentos incorrectos. Estas situaciones requieren información adicional sobre el contexto en el que aparecen los identificadores.

Por esta razón, el proyecto complementa el análisis léxico y sintáctico con un análisis semántico y una tabla de símbolos. Esta combinación permite controlar las declaraciones, los tipos y los ámbitos, demostrando que la construcción de un analizador de lenguaje no depende de una sola gramática, sino de varias etapas que trabajan en conjunto para verificar diferentes propiedades del programa.