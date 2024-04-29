#ifndef __NEURAL_NETWORK_LAYER_HPP__
#define __NEURAL_NETWORK_LAYER_HPP__

#include <vector>

#include "Neuron.hpp"

class NeuralNetworkLayer : public std::vector<Neuron> {
private:
    Neuron biasNeuron;
public:
    NeuralNetworkLayer(unsigned numNeurons);
    Neuron& getBiasNeuron() { return biasNeuron; }
};

#endif