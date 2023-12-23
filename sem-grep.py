from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
from tqdm import tqdm
import numpy as np
import os

documents = {}
for filename in os.listdir("documents"):
    with open(f"documents/{filename}", "r") as f:
        documents[filename] = f.read()

def split_text_into_chapters(text):
    """
    Finds a heading and split the text into chapters.
    """

    chapters = []
    chapter = []
    for line in text.splitlines():
        if line.startswith("#"):
            chapters.append("\n".join(chapter))
            chapter = []
        if line != "":
            chapter.append(line)
    chapters.append("\n".join(chapter))

    return chapters[1:]

def text_into_sentences(text):
    """
    Splits text into sentences.

    Splits on punctuation and newlines.
    """
    sentences = []

    for line in text.splitlines():
        sentences.extend(line.split(". "))
    return sentences

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def embed_documents(documents):
    """
    Embeds a dictionary of documents.
    """
    embeddings = {} # filename -> [embedding]
    for filename, text in tqdm(documents.items()):
        chapters = split_text_into_chapters(text)
        chapter_embeddings = []
        for chapter in chapters:
            sentences_embeddings = model.encode(text_into_sentences(chapter))
            average_embedding = np.mean(sentences_embeddings, axis=0)
            chapter_embeddings.append(average_embedding)
        embeddings[filename] = chapter_embeddings
    return embeddings

def search(query, documents_embeddings, n=1):
    """
    Searches the documents for the query.

    query: str
        The query to search for.
    documents_embeddings: dict[str, list[float]]
    """
    query_embedding = model.encode([query])[0]

    # Compare the query embedding with the document embeddings
    distances = {}
    for filename, chapter_embeddings in documents_embeddings.items():
        best_score = 0
        best_chapter = 0
        for chapter_idx, chapter_embedding in enumerate(chapter_embeddings):
            score = 1 - cosine(query_embedding, chapter_embedding)
            if score > best_score:
                best_score = score
                best_chapter = chapter_idx
        distances[filename] = (best_score, best_chapter)

    # Sort the distances
    sorted_distances = sorted(distances.items(), key=lambda x: x[1][0], reverse=True)

    # Print the top n results
    for filename, distance in sorted_distances[:n]:
        print(f"Best match: {filename} with score {distance[0]} in chapter {distance[1]}")
        document = documents[filename]
        chapters = split_text_into_chapters(document)
        print(chapters[distance[1]])

doc_emb = embed_documents(documents)

if __name__ == "__main__":
    search("Hard problem to solve", doc_emb)
