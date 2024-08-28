import csv
import matplotlib.pyplot as plt
import numpy as np

# Fixing random state for reproducibility
#np.random.seed(19680801)

with open('olympic2012.csv', newline='') as csvfile:
    data = list(csv.reader(csvfile))

print(data)

data = np.array(data)

x, y = data.T  # transpose

color = '#0000ff'
area = 2

print("Array x: ", x)
print("Array y: ", y)
print("Array color: ", color)

plt.scatter(x, y, s=area, c=color, alpha=0.5)
plt.show()

