// Programa con un ERROR LÉXICO para la demostración.
// El lexer se detiene en la línea 8: '12abc' no es un número válido.
#include <iostream>
using namespace std;

int main() {
    int total = 0;
    int cantidad = 12abc;
    total = total + cantidad;
    return 0;
}

// Otros errores léxicos que se pueden probar cambiando la línea 8:
//   int cantidad = 3 @ 4;      -> carácter no válido '@'
//   float cantidad = 1.2.3;    -> número mal formado '1.2.3'
//   int cantidad = 1; /* ...   -> comentario sin cerrar
