import pickle
import matplotlib.pyplot as plt
import sys

filename = sys.argv[1]
with open(filename, "rb") as f:
    fig = pickle.load(f)

plt.show()
