#include <iostream>
#include "NeuralNetwork.hpp"

void try1() {
    std::vector<uint> topology = {2, 3, 1};
    NeuralNetwork nn(topology);
    std::cout << nn << std::endl;
}

int main() {
    try1();
    return 0;
}