#include "Neuron.hpp"
#include "NeuralNetworkLayer.hpp"

#include <log4cpp/Category.hh>
#include <cmath>

Neuron::Neuron(double output, unsigned numWeights)
    : output(output), weights(numWeights)
{
    // Initialize weights with random values
    for (unsigned i = 0; i < numWeights; i++) {
        weights[i] = Neuron::randomWeight();
    }
}

void Neuron::feedForward(const NeuralNetworkLayer& prevLayer, unsigned neuronIndex) {
    log4cpp::Category& root = log4cpp::Category::getRoot();
    root.debug("Neuron::feedForward()");

    double sum = 0.0;

    for (unsigned i = 0; i < prevLayer.size(); i++) {
        sum += prevLayer[i].getOutput() * prevLayer[i].getWeight(neuronIndex);
    }

    output = Neuron::activationFunction(sum);
    root.debug("Neuron::feedForward() output=" + std::to_string(output));
}

double Neuron::activationFunction(double x) {
    log4cpp::Category& root = log4cpp::Category::getRoot();
    root.debug("Neuron::activationFunction(" + std::to_string(x) + ")");
    return tanh(x);
}