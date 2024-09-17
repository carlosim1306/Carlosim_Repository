#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <time.h>

int main(int argc, char* argv[]) {
    unsigned short xi[3] = { 1, 2, 3 };
    unsigned long long count = 0;
    long long i;
    long long samples;
    double x, y;
    double start_time, end_time;
    long long num_steps = 10000000;
    double step, pi;
    double sum = 0.0;

#define MAX_THREADS 8

    printf("Número de hilos: %d\n", MAX_THREADS);

    printf("num_steps, Estimación pi, Diferencia pi, Tiempo de ejecución\n");
    for (int row = 0; row < 10; row++) {

        step = 1.0 / (double)num_steps;
        sum = 0;
        start_time = omp_get_wtime();

        omp_set_num_threads(MAX_THREADS); //p=número de hilos
        
#pragma omp parallel for shared(step) reduction(+:sum)
            for (i = 0; i < num_steps; i++) {
                double x = (i + 0.5) * step;
                sum += 4.0 / (1.0 + x * x);
            }
        pi = step * sum;
        end_time = omp_get_wtime();
        

        double difference = 3.1415926 - pi;
        double execution_time = end_time - start_time;

        printf("%lld,%.7f,%.7f,%.7f\n", num_steps, pi, difference, execution_time);

        // Incrementa el número de samples para la próxima iteración
        num_steps *= 2;
    }
    return 0;
}
