#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <mpi.h>

int main(int argc, char* argv[]) {
    int rank, size;
    unsigned short xi[3] = { 1, 2, 3 };
    long long i;
    long long num_steps = 10000000;
    double step, pi;
    double sum = 0.0;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

#define MAX_THREADS 4

    if (rank == 0) {
        printf("Número de procesos: %d\n", size);
        printf("Número de hilos: %d\n", MAX_THREADS);
        printf("num_steps, Estimación pi, Diferencia pi, Tiempo de ejecución\n");
    }

    for (int row = 0; row < 10; row++) {
        step = 1.0 / (double)num_steps;
        sum = 0;

        double start_time = MPI_Wtime();

        omp_set_num_threads(MAX_THREADS); //p=número de hilos

#pragma omp parallel for shared(step) reduction(+:sum)
        for (i = rank; i < num_steps; i += size) {
            double x = (i + 0.5) * step;
            sum += 4.0 / (1.0 + x * x);
        }

        double local_pi = step * sum;
        MPI_Reduce(&local_pi, &pi, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

        double end_time = MPI_Wtime();

        if (rank == 0) {
            double difference = 3.1415926 - pi;
            double execution_time = end_time - start_time;
            printf("%lld,%.7f,%.7f,%.7f\n", num_steps, pi, difference, execution_time);
        }

        // Incrementa el número de steps para la próxima iteración
        num_steps *= 2;
    }

    MPI_Finalize();

    return 0;
}