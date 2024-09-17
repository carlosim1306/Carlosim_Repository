#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <time.h>

int main(int argc, char* argv[]) {
    unsigned long long count = 0;
    long long i;
    long long samples;
    double x, y;
    double start_time, end_time;
    double step, pi;
    double sum = 0.0;

#define MAX_THREADS 4
    samples = 10000000; /* Valor por defecto */

    printf("Prueba para %1d hilos\n", MAX_THREADS);
    printf("Samples, Estimación pi, Diferencia pi, Tiempo de ejecución\n");

    for (int row = 0; row < 10; row++) {
        count = 0;

        // Establecer una semilla única para cada hilo antes de entrar al bucle paralelo
        unsigned int seeds[MAX_THREADS];
        for (int j = 0; j < MAX_THREADS; j++) {
            seeds[j] = (unsigned int)(j + 1);
        }

        start_time = omp_get_wtime();

#pragma omp parallel 
        {
            unsigned int seed = seeds[omp_get_thread_num()];
            srand(seed);

#pragma omp for  reduction (+:count) 
            for (i = 0; i < samples; ++i) {
                double x, y, z;
                x = ((double)rand()) / ((double)RAND_MAX);
                y = ((double)rand()) / ((double)RAND_MAX);
                z = x * x + y * y;
                if (z <= 1.0) {
                    ++count;
                }
            }
        }

        end_time = omp_get_wtime(); // Fin del tiempo de ejecución

        double pi = 4.0 * count / samples;
        double difference = 3.1415926 - pi;
        double execution_time = end_time - start_time;

        printf("%lld,%.7f,%.7f,%.7f\n", samples, pi, difference, execution_time);

        // Incrementa el número de samples para la próxima iteración
        samples *= 2;
    }

    return 0;
}
