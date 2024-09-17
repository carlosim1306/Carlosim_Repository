#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char* argv[]) {
    unsigned short xi[3] = { 1, 2, 3 };
    unsigned long long count = 0;
    long long i;
    long long samples;
    double x, y;
    double start_time, end_time;
    double sum = 0.0;

    samples = 10000000; /* Valor por defecto */
    printf("Samples, Estimación pi, Diferencia pi, Tiempo de ejecución\n");

    for (int row = 0; row < 10; row++) {
        count = 0;
        start_time = clock();

        for (i = 0; i < samples; ++i) {
            x = ((double)rand()) / ((double)RAND_MAX); // 0≤x≤1
            y = ((double)rand()) / ((double)RAND_MAX);
            if (x * x + y * y <= 1.0) {
                ++count;
            }
        }

        end_time = clock();
        double pi = 4.0 * count / samples;
        double difference = 3.1415926 - pi;
        double execution_time = (end_time - start_time)/1000;

        printf("%lld,%.7f,%.7f,%.7f\n", samples, pi, difference, execution_time);

        // Incrementa el número de samples para la próxima iteración
        samples *= 2;
    }
    return 0;
}
