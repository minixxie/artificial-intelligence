# Define the Docker image name and tag
IMAGE_NAME := my-docker-image
IMAGE_TAG := latest

# Define the Dockerfile path
DOCKERFILE := Dockerfile

.PHONY: build run

build:
	# Build the Docker image
	nerdctl build -t $(IMAGE_NAME):$(IMAGE_TAG) -f $(DOCKERFILE) .

run:
	# Run the Docker image
	nerdctl run $(IMAGE_NAME):$(IMAGE_TAG)
