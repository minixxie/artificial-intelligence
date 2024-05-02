#include "NeuralNetwork.hpp"

#include <log4cpp/Category.hh>
#include <log4cpp/Priority.hh>
#include <log4cpp/OstreamAppender.hh>
#include <log4cpp/PatternLayout.hh>
#include <iostream>

void try1() {
    log4cpp::Category& root = log4cpp::Category::getRoot();

    std::vector<uint> topology = {2, 3, 1};
    NeuralNetwork nn(topology);
    root << log4cpp::Priority::INFO << '\n' << nn;

    nn.feedForward({3.14159, 2.71828});
    root << log4cpp::Priority::INFO << '\n' << nn;
}

void setupLogging() {
    log4cpp::OstreamAppender* osAppender = new log4cpp::OstreamAppender("osAppender", &std::cout);
    log4cpp::PatternLayout* layout = new log4cpp::PatternLayout();
    layout->setConversionPattern("%d: %p %c %x: %m%n");
    osAppender->setLayout(layout);

    log4cpp::Category& root = log4cpp::Category::getRoot();
    root.addAppender(osAppender);
    root.setPriority(log4cpp::Priority::INFO);
}

void cleanupLogging() {
    log4cpp::Category::shutdown();
}

int main() {
    setupLogging();

    try1();

    cleanupLogging();
    return 0;
}