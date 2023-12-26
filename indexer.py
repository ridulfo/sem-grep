"""
This file contains functions to create the semantic-grep index.

Compared to normal grep, semantic search requires more computation. Therefore,
we create an index in the local directory in order to keep searches fast.

The index consists of a hash of a file's contents and the embeddings associated
to that file.

"""

import os
from embed import embed_document, split_text_into_chapters
from tqdm import tqdm
import pickle
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
from dataclasses import dataclass


INDEX_FILE = ".sem-grep.index"

def _find_all_files(path="."):
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


def _hash_content(text):
    """
    Hash the contents of a file.
    """
    return hash(text)


def index_files(path="."):
    """
    Index all files in a directory.
    """
    files = _find_all_files(path)

    index = {}

    for file_path in tqdm(files, desc="Indexing files"):
        with open(file_path, "r") as f:
            document_text = f.read()

        hash = _hash_content(document_text)
        chapter_embeddings = embed_document(document_text)

        index[hash] = (file_path, chapter_embeddings)

    return index


class Index:
    model = None
    def __init__(self, path="."):
        self.path = path
        if os.path.exists(os.path.join(self.path, INDEX_FILE)):
            self.index = self._load_index()
        else:
            self.index = index_files(self.path)
            self._save_index()
    
    def _load_index(self):
        """
        Load the index from disk.
        """
        with open(os.path.join(self.path, INDEX_FILE), "rb") as f:
            # TODO: check for file changes before returning
            return pickle.load(f)
    
    def _save_index(self):
        """
        Save the index to disk.
        """
        with open(os.path.join(self.path, INDEX_FILE), "wb") as f:
            pickle.dump(self.index, f)
    
    def search(self, query, n=1):
        """
        Searches the documents for the query.

        query: str
            The query to search for.
        documents_embeddings: dict[str, list[float]]
        """

        if not self.model:
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        query_embedding = self.model.encode([query])[0]

        # Compare the query embedding with the document embeddings
        distances = {}
        for _, content in tqdm(self.index.items(), desc="Searching"):
            filename, chapter_embeddings = content

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
            with open(filename, "r") as f:
                document = f.read()
            chapters = split_text_into_chapters(document)
            print(chapters[distance[1]])
