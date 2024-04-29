#ifndef __NEURON_HPP__
#define __NEURON_HPP__

class Neuron {
private:
    double activationValue;
public:
    explicit Neuron(double activationValue);
    double getActivationValue() const { return activationValue; }
};

#endif