#ifndef __NEURON_HPP__
#define __NEURON_HPP__

#include <vector>
#include <cstdlib>

class NeuralNetworkLayer;

class Neuron {
private:
    unsigned neuronIndex;
    double output;
    std::vector<double> weights;
public:
    explicit Neuron(unsigned neuronIndex, double output, unsigned numWeights = 0);

    double getOutput() const { return output; }
    void setOutput(double output) { this->output = output; }

    static double randomWeight() { return rand() / double(RAND_MAX); }
    double getWeight(unsigned index) const { return weights[index]; }

    void feedForward(const NeuralNetworkLayer& prevLayer);

    static double activationFunction(double x);
};

#endif