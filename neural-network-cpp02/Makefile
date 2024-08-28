.PHONY: bash
bash:
	nerdctl run --rm -it -v "$$PWD":/usr/src/app -w /usr/src/app ubuntu:22.04 bash

.PHONY: compile
compile: NeuralNetwork.o

.PHONY: NeuralNetwork.o
NeuralNetwork.o: NeuralNetwork.cpp NeuralNetwork.hpp
	g++ -c NeuralNetwork.cpp


