.PHONY: bash
bash:
	nerdctl run --rm -it -v "$$PWD":/usr/src/app -w /usr/src/app ubuntu:22.04 bash

.PHONY: link
link: compile
	g++ -o main \
		-static \
		NeuralNetwork.o main.o

.PHONY: compile
compile: NeuralNetwork.o main.o

NeuralNetwork.o: NeuralNetwork.cpp NeuralNetwork.hpp
	g++ -c NeuralNetwork.cpp

main.o: main.cpp NeuralNetwork.hpp
	g++ -c main.cpp

.PHONY: build
build:
	nerdctl build . \
		-f Containerfile \
		-t neural-network-cpp:dont_push

.PHONY: run
run: build
	nerdctl run --rm -it neural-network-cpp:dont_push

.PHONY: show-img
show-img:
	nerdctl images | grep neural-network-cpp