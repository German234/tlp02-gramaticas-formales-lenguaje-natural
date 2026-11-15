// Programa con un ERROR SEMÁNTICO para la demostración.
// El lexer y el parser lo aceptan (es sintácticamente correcto), pero
// en la línea 13 se usa 'contador' fuera del bloque donde fue declarado.
#include <iostream>
using namespace std;

int main() {
    int total = 0;
    {
        int contador = 5;
        total = total + contador;
    }
    contador = contador + 1;
    return 0;
}

// Otros errores semánticos que se pueden probar cambiando la línea 13:
//   int total = 1;          -> redeclaración en el mismo ámbito
//   bool listo = 4;         -> no se puede asignar int a bool
//   if (total) total = 1;   -> la condición debe ser de tipo bool
//   break;                  -> 'break' fuera de un ciclo o switch
