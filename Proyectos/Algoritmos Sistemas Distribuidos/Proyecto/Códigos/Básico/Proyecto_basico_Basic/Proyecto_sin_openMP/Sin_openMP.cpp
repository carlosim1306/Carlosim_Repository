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
    long long num_steps = 10000000;
    double step, pi;
    double sum = 0.0;


    printf("num_steps, Estimación pi, Diferencia pi, Tiempo de ejecución\n");
    for (int row = 0; row < 10; row++) {
        pi = 0.;
        step = 0.;
        sum = 0.;

        start_time = clock();

        step = 1.0 / (double)num_steps;
        for (i = 0;i < num_steps;i++) {
            x = (i + 0.5) * step;
            sum = sum + 4.0 / (1.0 + x * x);
        }
        pi = step * sum;

        end_time = clock();

        double difference = 3.1415926 - pi;
        double execution_time = (end_time - start_time) / 1000;

        printf("%lld,%.7f,%.7f,%.7f\n", num_steps, pi, difference, execution_time);

        // Incrementa num_steps para la próxima iteración
        num_steps *= 2;
    }

    return 0;
}
