/*
 * Programa de ejemplo que usa todo el subconjunto de C++ soportado:
 * tipos, funciones, operadores, estructuras de control y ámbitos.
 */
#include <iostream>
using namespace std;

// Función con parámetros y retorno int
int sumar(int a, int b) {
    return a + b;
}

// Función recursiva
int factorial(int n) {
    if (n <= 1)
        return 1;
    return n * factorial(n - 1);
}

// Retorno float: int se promueve a float
float promedio(int total, int cantidad) {
    float resultado = total;
    return resultado / cantidad;
}

// Retorno bool con operadores lógicos y de igualdad
bool esPar(int n) {
    return n % 2 == 0 && !(n < 0);
}

// Función void con return vacío
void reiniciar(int valor) {
    valor = 0;
    return;
}

int main() {
    // Declaraciones de los tres tipos
    int total = 0;
    int contador = 10;
    float precio = 2.5;
    bool listo = true;

    // Expresiones con precedencia, paréntesis y menos unario
    float descuento = -precio * (3 + 1) / 2;
    bool rango = total >= 0 || contador != 5;

    // Ciclo for: 'i' solo existe dentro del for
    for (int i = 0; i < 3; i++) {
        total = total + sumar(i, 1);
    }

    // Ciclo while sin llaves y decremento
    while (contador > 7)
        contador--;

    // do-while con break
    do {
        contador = contador - 1;
        if (contador == 2)
            break;
    } while (contador > 0);

    // if / else anidados (else colgante: pertenece al if interno)
    if (listo)
        if (total > 5)
            total = total + 1;
        else
            total = total - 1;

    // switch con case negativo, default y break
    int opcion = factorial(3);
    switch (opcion) {
        case 6:
            precio = promedio(total, 2);
            break;
        case -1:
            precio = 0;
            break;
        default:
            precio = 1.0;
    }

    // Ámbitos: 'total' interno (bool) oculta al externo (int)
    {
        bool total = esPar(opcion);
        listo = total;
    }
    total = total + 1;   // aquí 'total' vuelve a ser el int externo

    reiniciar(total);    // llamada a función void como sentencia
    return 0;
}
