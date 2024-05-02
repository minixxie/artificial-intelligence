#ifndef __NEURAL_NETWORK_HPP__
#define __NEURAL_NETWORK_HPP__

#include <iostream>
#include <vector>

#include "NeuralNetworkLayer.hpp"

class NeuralNetwork {
private:
    /*
        e.g. if topology = [2, 3, 1] then the network has 2 input neurons, 3 neurons in hidden layer
        3 elements in topology also means the neural-network has 3 layers
        then in constructor, it will initialize neuronLayers as follows:
        neuronLayers = [
            [A, A],     // input layer, 2 neurons
            [A, A, A],  // hidden layer, 3 neurons
            [A]         // output layer, 1 neuron
        ]
        each A stored is "activationValue" of the neuron
    */
    std::vector<uint> topology;
    std::vector<NeuralNetworkLayer> neuronLayers;
public:
    // Constructor
    NeuralNetwork(const std::vector<uint>& topology);

    friend std::ostream& operator<<(std::ostream& os, const NeuralNetwork& nn);

    void feedForward(const std::vector<double>& inputVals);
};

std::ostream& operator<<(std::ostream& os, const NeuralNetwork& nn);

#endif