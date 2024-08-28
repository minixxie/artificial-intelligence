import numpy as np
from glove import Glove
from glove import Corpus

def generate_embeddings(text):
    # Create a corpus from the text
    corpus = Corpus()
    corpus.fit([text], window=10)

    # Train the GloVe model
    glove = Glove(no_components=100, learning_rate=0.05)
    glove.fit(corpus.matrix, epochs=30, no_threads=4, verbose=True)
    glove.add_dictionary(corpus.dictionary)

    # Generate embeddings for the text
    embeddings = []
    for word in text.split():
        if word in glove.dictionary:
            embeddings.append(glove.word_vectors[glove.dictionary[word]])

    return np.array(embeddings)

# Example usage
text = "This is an example sentence."
embeddings = generate_embeddings(text)
print(embeddings)