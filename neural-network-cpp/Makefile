SHELL := /bin/bash
COMPILE_OPTIONS = -Wall -Wextra -Wpedantic -Werror -std=c++20 -O3 -fPIC

.PHONY: bash
bash:
	nerdctl run --rm -it -v "$$PWD":/usr/src/app -w /usr/src/app ubuntu:22.04 bash

.PHONY: link
link: compile
	g++ -static -o main \
		NeuralNetwork.o NeuralNetworkLayer.o Neuron.o main.o \
		$$(find /usr/lib -name liblog4cpp.a)

.PHONY: compile
compile: NeuralNetwork.o NeuralNetworkLayer.o Neuron.o main.o

NeuralNetwork.o: NeuralNetwork.cpp NeuralNetwork.hpp
	g++ -c ${COMPILE_OPTIONS} NeuralNetwork.cpp

NeuralNetworkLayer.o: NeuralNetworkLayer.cpp NeuralNetworkLayer.hpp
	g++ -c ${COMPILE_OPTIONS} NeuralNetworkLayer.cpp

Neuron.o: Neuron.cpp Neuron.hpp
	g++ -c ${COMPILE_OPTIONS} Neuron.cpp

main.o: main.cpp NeuralNetwork.hpp
	g++ -c ${COMPILE_OPTIONS} main.cpp

.PHONY: build
build:
	nerdctl build . \
		-f Containerfile \
		-t neural-network-cpp:dont_push
	nerdctl images | grep neural-network-cpp

.PHONY: run
run: build
	nerdctl run --rm -it neural-network-cpp:dont_push

.PHONY: show-img
show-img:
	nerdctl images | grep neural-network-cpp