#ifndef __NEURAL_NETWORK_LAYER_HPP__
#define __NEURAL_NETWORK_LAYER_HPP__

#include <vector>

#include "Neuron.hpp"

class NeuralNetworkLayer : public std::vector<Neuron> {
private:
    bool hasBias;
public:
    NeuralNetworkLayer(unsigned numNeurons, bool hasBias, unsigned numWeightsPerNeuron);
    bool getHasBias() const { return this->hasBias; }
    Neuron& getBiasNeuron() { return (*this).back(); }

    void feedForward(const NeuralNetworkLayer& prevLayer);
};

#endif