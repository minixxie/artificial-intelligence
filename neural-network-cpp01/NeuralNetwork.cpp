#include "NeuralNetwork.hpp"
#define PRINT_NEURON_INDEX 1

#include <iomanip>

std::ostream& operator<<(std::ostream& os, const NeuralNetworkData& nn) {
    for (uint i = 0; i < nn.size(); i++) {
        os << "Layer " << i << ": " << std::endl;
		if (PRINT_NEURON_INDEX == 1) {
			for (uint j = 0; j < nn[i]->size(); j++) {
				os << "[" << j << ": " << nn[i]->coeff(j) << "] ";
			}
			os << std::endl;
		} else {
			os << *nn[i] << std::endl;
		}
    }
    return os;
}

/**
 * Overloaded insertion operator for output stream.
 * Prints the neural network object in a formatted manner.
 *
 * @param os The output stream to write to.
 * @param nn The NeuralNetwork object to be printed.
 * @return The modified output stream.
 */
std::ostream& operator<<(std::ostream& os, const NeuralNetwork& nn) {
	/*
	print nn.neuralLayers, each layer printed vertically. each layer's neuron occupies 10 character spaces. the next layer will be using the next 10 character spaces. So the printing sequence of first line of output will be, the 1st neuron of 1st layer, then 1st neuron of the 2nd layer, then 1st neuron of the 3rd layer, and so on.
2nd line of output will be 2nd neuron of 1st layer, 2nd neuron of the 2nd layer, 2nd neuron of the 3rd layer, and so on.
	*/

	uint maxNumElements = 0;
	for (const auto& layer : nn.neuronLayers) {
		maxNumElements = std::max(maxNumElements, (uint)layer->size());
	}

	for (uint j = 0; j < nn.neuronLayers.size(); j++) {
		os << "{" << std::left << std::setw(13);
		if (j == 0) {
			os << "Input Layer";
		} else if (j == nn.neuronLayers.size() - 1) {
			os << "Output Layer";
		} else {
			os << "Hidden Layer";
		}
		os << "}";
		if (j != nn.neuronLayers.size() - 1) {
			os << "     ";
		}
	}
	os << std::endl;
	for (uint j = 0; j < nn.neuronLayers.size(); j++) {
		os << "---------------";
		if (j != nn.neuronLayers.size() - 1) {
			os << "     ";
		}
	}
	os << std::endl;

	for (uint i = 0; i < maxNumElements; i++) {
		for (uint j = 0; j < nn.neuronLayers.size(); j++) {
			if (i < nn.neuronLayers[j]->size()) {
				os << std::right << std::setfill('0') << std::setw(2) << i
					<< " [" << std::left << std::setfill(' ') << std::setw(10) << nn.neuronLayers[j]->coeff(i);

				if (i == nn.neuronLayers[j]->size() - 1
					&& j != nn.neuronLayers.size() - 1) {
					os << "]bias ";
				} else {
					os << "]     ";
				}
			} else {
				os << "                    ";
			}
		}
		os << std::endl;
	}

	// for (uint i = 0; i < nn.neuronLayers.size(); i++) {
	// 	os << "00[" << nn.neuronLayers[i]->coeff(0) << "]";

	// 	os << "Layer " << i << ": " << std::endl;
	// 	if (PRINT_NEURON_INDEX == 1) {
	// 		for (uint j = 0; j < nn.neuronLayers[i]->size(); j++) {
	// 			os << "[" << j << ": " << nn.neuronLayers[i]->coeff(j) << "] ";
	// 		}
	// 		os << std::endl;
	// 	} else {
	// 		os << *nn.neuronLayers[i] << std::endl;
	// 	}
	// }

	return os;
}

// constructor of neural network class
NeuralNetwork::NeuralNetwork(std::vector<uint> topology, Scalar learningRate)
{
	this->topology = topology;
	this->learningRate = learningRate;
	for (uint i = 0; i < topology.size(); i++) {
		// initialize neuron layers
		if (i == topology.size() - 1) {
			// output layer doesn't have bias neuron
			neuronLayers.push_back(new RowVector(topology[i]));
		} else {
			// for +1: add an extra neuron for bias
			neuronLayers.push_back(new RowVector(topology[i] + 1));
		}

		// initialize cache and delta vectors
		cacheLayers.push_back(new RowVector(neuronLayers.size()));
		deltas.push_back(new RowVector(neuronLayers.size()));

		// vector.back() gives the handle to recently added element
		// coeffRef gives the reference of value at that place 
		// (using this as we are using pointers here)
		if (i != topology.size() - 1) {
			neuronLayers.back()->coeffRef(topology[i]) = 1.0;
			cacheLayers.back()->coeffRef(topology[i]) = 1.0;
		}

		// initialize weights matrix
		if (i > 0) {
			if (i != topology.size() - 1) {
				weights.push_back(new Matrix(topology[i - 1] + 1, topology[i] + 1));
				weights.back()->setRandom();
				weights.back()->col(topology[i]).setZero();
				weights.back()->coeffRef(topology[i - 1], topology[i]) = 1.0;
			}
			else {
				weights.push_back(new Matrix(topology[i - 1] + 1, topology[i]));
				weights.back()->setRandom();
			}
		}
	}
};

void NeuralNetwork::printWeightsMatrix(std::ostream& os) {
	for (uint i = 0; i < weights.size(); i++) {
		os << "Layer " << i << ": " << std::endl;
		os << "--------" << std::endl;
		os << *weights[i] << std::endl;
	}
}