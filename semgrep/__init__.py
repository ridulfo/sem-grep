#! env/bin/python3

import argparse
from dataclasses import dataclass
from hashlib import md5
import os
import pickle
from typing import Dict, List, Optional

import numpy as np
from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer
from torch.functional import Tensor
from tqdm import tqdm

INDEX_FILE_NAME = ".semgrep-index"

@dataclass
class Document:
    path: str
    embeddings: Optional[List[Tensor]]

index_t = Dict[bytes, Document] # hash digest -> Document


def find_all_files(path="."):
    """
    Recursively find all files in a directory.
    """
    files = []
    for root, _, file_names in os.walk(path):
        for file_name in file_names:
            # TODO: create different splitters for different file types
            if file_name.endswith(".md"):
                files.append(os.path.join(root, file_name))
    return files


def embed_document(model, document_text):
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


def create_empty_index(search_path):
    files = find_all_files(search_path)
    index:index_t = {}

    for file_path in tqdm(files, desc="Hashing files"):
        with open(file_path, "r") as f:
            document_text = f.read()

        hash = md5(document_text.encode()).digest()

        index[hash] = Document(file_path, None)

    return index


def transfer_embeddings(old_index: index_t, new_index: index_t):
    for hash, document in new_index.items():
        if hash in old_index:
            document.embeddings = old_index[hash].embeddings

def embed_missing_documents(index: index_t, model):
    documents_to_embed = list(filter(lambda d: not d.embeddings,  index.values()))
    if len(documents_to_embed)==0: return
    for document in tqdm(documents_to_embed, desc="Embeddings documents"):
        if not document.embeddings:
            with open(document.path) as f:
                document.embeddings = embed_document(model, f.read())


def save_index(index_path, index):
    with open(index_path, "wb") as f:
        pickle.dump(index, f)


def load_index(index_path):
    with open(index_path, "rb") as f:
        return pickle.load(f)


def search(index:index_t, query, n=1):
    """
    Searches the documents for the query.

    query: str
        The query to search for.
    documents_embeddings: dict[str, list[float]]
    """

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    query_embedding = model.encode([query])[0]

    # Compare the query embedding with the document embeddings
    distances = {}
    for _, document in tqdm(index.items(), desc="Searching"):
        best_score = 0
        best_chapter = 0

        if not document.embeddings:
            continue

        for chapter_idx, chapter_embedding in enumerate(document.embeddings):
            score = 1 - cosine(query_embedding, chapter_embedding)
            if score > best_score:
                best_score = score
                best_chapter = chapter_idx

        distances[document.path] = (best_score, best_chapter)

    # Sort the distances
    sorted_distances = sorted(distances.items(), key=lambda x: x[1][0], reverse=True)

    # Print the top n results
    for filename, distance in sorted_distances[:n]:
        print(f"{filename} with score {distance[0]} in chapter {distance[1]}")
        with open(filename, "r") as f:
            document = f.read()
        chapters = split_text_into_chapters(document)
        print(chapters[distance[1]], end="\n\n")

def main():
    parser = argparse.ArgumentParser(prog="Semantic grep", description="A semantic document search")
    parser.add_argument("query", type=str, help="The search query.")
    parser.add_argument("--update", "-u", action='store_true', help="Whether to update the index (might take some time).", default=False)
    parser.add_argument("--path", "-p", help="The directory to search.", default=".", type=str)
    parser.add_argument("-n", help="The number of results to return", default=1, type=int)
    
    args = parser.parse_args()
    query = args.query
    search_path = args.path
    should_update = args.update
    n = args.n

    index_path = os.path.join(search_path, INDEX_FILE_NAME)
    has_index = os.path.exists(index_path)
    
    if has_index:
        index = load_index(index_path)
    else:
        index = create_empty_index(search_path)
        should_update = True

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    if should_update:
        old_index = index
        index = create_empty_index(search_path) # hash -> (file name, None)
        transfer_embeddings(old_index, index)
        embed_missing_documents(index, model)
        save_index(index_path, index)
        
    search(index, query, n)

if __name__ == "__main__":
    main()
