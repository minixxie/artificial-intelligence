#include "NeuralNetworkLayer.hpp"
#include "Neuron.hpp"

NeuralNetworkLayer::NeuralNetworkLayer(unsigned numNeurons)
    : std::vector<Neuron>(numNeurons, Neuron(0.0)),
      biasNeuron(1.0) {
}