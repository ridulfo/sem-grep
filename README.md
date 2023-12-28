# Semantic grep

- Local semantic search
- Local "database"
- Low code complexity
- Sub 300 lines of code

Because of the sentive nature of personal files, the number of lines of code will be kept low in order for the project to easily be audited and understood.

## Installation and updating
`pip install -U git+https://github.com/ridulfo/sem-grep`


## Usage

```
semgrep -h
usage: Semantic grep [-h] [--update] [--path PATH] [-n N] query

A semantic document search

positional arguments:
  query                 The search query.

options:
  -h, --help            show this help message and exit
  --update, -u          Whether to update the index (might take some time).
  --path PATH, -p PATH  The directory to search.
  -n N                  The number of results to return
```

**Example**

`semgrep -u -p document-directory -n 4 "search query"`

## How it works

### First time
1. Create an empty index by recursively finding all files and hashing their content. The hash-digest will be used as key in the index.
2. For every file, segment and embed the documents
3. Save a cache of the index in the search directory for future searches
4. Run vector similarity search on the embeddings
5. Display the matches

### Other times (when a cache is already present in the search directory)

1. Look for a cached index
2. If the update flag is raised
	1. Create an empty index by recursively finding all files and hashing their content.
	2. For the files that have not changed, move over the embeddings from the cache.
	3. Embed the files that have changed.
3. Save a cache of the index in the search directory for future searches
4. Run vector similarity search on the embeddings
5. Display the matches
