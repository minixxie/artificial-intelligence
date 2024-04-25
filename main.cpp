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

int main() {
    try2();
    return 0;
}