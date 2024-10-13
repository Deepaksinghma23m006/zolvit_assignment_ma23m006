
from haystack.nodes import PDFToTextConverter, PreProcessor, EmbeddingRetriever
from haystack.document_stores import WeaviateDocumentStore
from haystack.pipelines import DocumentSearchPipeline
import box
import yaml
import timeit
import os

with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))

def run_ingest():
    file_list = [os.path.join(cfg.DATA_PATH, f) for f in os.listdir(cfg.DATA_PATH) if
                os.path.isfile(os.path.join(cfg.DATA_PATH, f)) and not f.startswith('.')]

    start = timeit.default_timer()

    vector_store = WeaviateDocumentStore(
        host=cfg.WEAVIATE_HOST,
        port=cfg.WEAVIATE_PORT,
        embedding_dim=cfg.WEAVIATE_EMBEDDING_DIM
    )

    # Initialize PDF converter
    converter = PDFToTextConverter()

    # Convert PDFs to documents
    docs = []
    for file_path in file_list:
        try:
            documents = converter.convert(file_path=file_path, meta=None)
            docs.extend(documents)
        except Exception as e:
            print(f"Error converting {file_path}: {e}")

    # Preprocess documents
    preprocessor = PreProcessor(
        clean_empty_lines=True,
        clean_whitespace=False,
        clean_header_footer=False,
        split_by="word",
        language="en",
        split_length=cfg.PRE_PROCESSOR_SPLIT_LENGTH,
        split_overlap=cfg.PRE_PROCESSOR_SPLIT_OVERLAP,
        split_respect_sentence_boundary=True,
    )

    preprocessed_docs = preprocessor.process(docs)
    vector_store.write_documents(preprocessed_docs)

    # Initialize Retriever
    retriever = EmbeddingRetriever(
        document_store=vector_store,
        embedding_model=cfg.EMBEDDINGS
    )
    vector_store.update_embeddings(retriever)

    end = timeit.default_timer()
    print(f"Time to prepare embeddings: {end - start} seconds")

if __name__ == "__main__":
    run_ingest()
