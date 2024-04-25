#ifndef __NEURAL_NETWORK_HPP__
#define __NEURAL_NETWORK_HPP__

#include <eigen3/Eigen/Eigen>
#include <iostream>
#include <vector>

typedef float Scalar;
typedef Eigen::MatrixXf Matrix;
typedef Eigen::RowVectorXf RowVector;
typedef Eigen::VectorXf ColVector;

class NeuralNetwork {
public:
    // Constructor
    NeuralNetwork(std::vector<uint> topology, Scalar learningRate = Scalar(0.005));

    // function for forward propagation of data
    void propagateForward(RowVector& input);

    // function for backward propagation of errors made by neurons
    void propagateBackward(RowVector& output);

    // function to calculate errors made by neurons in each layer
    void calcErrors(RowVector& output);

    // function to update the weights of connections
    void updateWeights();

    // function to train the neural network give an array of data points
    void train(std::vector<RowVector*> data);

    // storage objects for working of neural network
    /*
        use pointers when using std::vector<Class> as std::vector<Class> calls destructor of 
        Class as soon as it is pushed back! when we use pointers it can't do that, besides
        it also makes our neural network class less heavy!! It would be nice if you can use
        smart pointers instead of usual ones like this
    */
    std::vector<RowVector*> neuronLayers; // stores the different layers of out network
    std::vector<RowVector*> cacheLayers; // stores the unactivated (activation fn not yet applied) values
    std::vector<RowVector*> deltas; // stores the error contribution of each neurons
    std::vector<Matrix*> weights; // the connection weights itself
    Scalar learningRate;
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
};

#endif