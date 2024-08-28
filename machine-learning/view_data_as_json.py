import json
from sklearn.datasets import load_digits
from sklearn.utils import Bunch
import numpy as np

# Load the digits dataset
digits = load_digits()

# Convert Bunch to dict
digits_dict = {key: value.tolist() if isinstance(value, np.ndarray) else value for key, value in digits.items()}

# Convert dict to JSON
digits_json = json.dumps(digits_dict)

print(digits_json)
