import sys
from indexer import Index

if __name__ == "__main__":
    index = Index(sys.argv[1])

    while True:
        query = input("Enter a query: ")
        results = index.search(query, n=1)
        print(results)
        print()
