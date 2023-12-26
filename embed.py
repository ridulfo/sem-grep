from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
import numpy as np

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


def embed_document(document_text):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    """
    Embeds a single document.
    """
    chapters = split_text_into_chapters(document_text)
    chapter_embeddings = []
    for chapter in chapters:
        sentences = text_into_sentences(chapter)
        sentences_embeddings = model.encode(sentences)
        average_embedding = np.mean(sentences_embeddings, axis=0)
        chapter_embeddings.append(average_embedding)
    
    return chapter_embeddings