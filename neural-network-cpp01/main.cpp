#include <iostream>
#include "NeuralNetwork.hpp"

void try1() {
    RowVector vector(5);
    vector << 1.20, 2.30, 3.40, 4.50, 5.60;
    std::cout << vector << std::endl;
}

void try2() {
    Eigen::Matrix2f m;
    m << 1, 2,
        3, 4;
    std::cout << "Before coeffRef: " << std::endl;
    std::cout << m << std::endl;
    m.coeffRef(0,1) += 5;

    std::cout << "After coeffRef: " << std::endl;
    std::cout << m << std::endl;

}
void try3() {
    // NeuralNetwork nn({12, 16, 10}, 0.005);
    NeuralNetwork nn({2, 3, 1}, 0.005);

	std::cout << "[Neural Network]" << std::endl;
    // std::cout << nn.neuronLayers << std::endl;
    std::cout << nn << std::endl;

	std::cout << "[Weights Matrices for each layer]" << std::endl;
    nn.printWeightsMatrix(std::cout);
}

int main() {
    try3();
    return 0;
}