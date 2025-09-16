#include <stdio.h>
#include <stdlib.h>

int main(int argc, char** argv) {
  if (argc < 3) {
    fprintf(stderr, "usage: sum <a> <b>\n");
    return 1;
  }
  double a = atof(argv[1]);
  double b = atof(argv[2]);
  printf("%f\n", a + b);
  return 0;
}
