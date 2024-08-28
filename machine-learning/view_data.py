# The load_digits() function returns a Bunch object that contains several fields. The most important ones are data and target.
# data is a 2D array where each row corresponds to an image, and each column is a pixel in that image. The images are 8x8 pixels, so there are 64 columns. The values are grayscale intensities.
# target is a 1D array that contains the labels for the images, i.e., the actual digits that the images represent.
# Here's how you can print the first two images and their labels:

from sklearn.datasets import load_digits
import matplotlib.pyplot as plt

# Load the digits dataset
digits = load_digits()

# Print the first two images
for i in range(2):
    print("loop...")
    print(f"Image {i+1}:")
    print(digits.data[i])
    print(f"Label: {digits.target[i]}")

    # Display the image
    plt.gray() 
    plt.matshow(digits.images[i]) 
    plt.show() 
