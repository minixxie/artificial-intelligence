#include "NeuralNetworkLayer.hpp"
#include "Neuron.hpp"

#include <iostream>
#include <log4cpp/Category.hh>

NeuralNetworkLayer::NeuralNetworkLayer(unsigned numNeurons, bool hasBias, unsigned numWeightsPerNeuron)
    : hasBias(hasBias)
{
  log4cpp::Category& root = log4cpp::Category::getRoot();
	root.debug("NeuralNetworkLayer::NeuralNetworkLayer()");

  // Initialize neurons with random weights
  unsigned totalNumNeurons = hasBias ? numNeurons + 1 : numNeurons;
  root << log4cpp::Priority::DEBUG << "NeuralNetworkLayer::NeuralNetworkLayer(): totalNumNeurons=" << totalNumNeurons;
  root << log4cpp::Priority::DEBUG << "NeuralNetworkLayer::NeuralNetworkLayer(): numWeightsPerNeuron=" << numWeightsPerNeuron;

  for (unsigned i = 0; i < totalNumNeurons; i++) {
    (*this).push_back(Neuron(i, 0.0, numWeightsPerNeuron));

  }
  if (hasBias) {
    // initialize bias neuron
    (*this).back().setOutput(1.0);
  }
}

void NeuralNetworkLayer::feedForward(const NeuralNetworkLayer& prevLayer) {
	log4cpp::Category& root = log4cpp::Category::getRoot();
	root.debug("NeuralNetworkLayer::feedForward()");

  unsigned totalNumNeurons = hasBias ? size() - 1 : size();
  root << log4cpp::Priority::DEBUG << "NeuralNetworkLayer::feedForward(): totalNumNeurons=" << totalNumNeurons;

  for (unsigned i = 0; i < totalNumNeurons; i++) {
    // skip bias neuron
    if (hasBias && i == size() - 1) {
      continue;
    }
    (*this)[i].feedForward(prevLayer);
  }
}