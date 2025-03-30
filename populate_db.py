import os
import logging

from langchain_postgres import PGVector
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from configs import config

MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class PopulateDatabase:
    def __init__(self) -> None:
        self.data_dir = 'datasets'

    @staticmethod
    def _get_vector_store(collection_name: str) -> PGVector:
        vector_store = PGVector(
            embeddings=HuggingFaceEmbeddings(model_name=MODEL_NAME),
            collection_name=collection_name,
            connection=config.postgres_url,
            use_jsonb=True,
        )

        return vector_store

    def load_datasets(self) -> None:
        """Загрузка всех датасетов из директории data"""
        dataset_files = os.listdir(self.data_dir)
        logger.info('Fetching the embedding model...')
        logger.info(f'Loading {len(dataset_files)} datasets')
        for filename in dataset_files:
            collection_name = filename.split('.')[0]
            vector_store = self._get_vector_store(collection_name)
            file_path = os.path.join(self.data_dir, filename)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File {file_path} not found.")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                chunks = content.split('\n\n')

            docs = []
            for idx, chunk in enumerate(chunks):
                query, context = chunk.split('\n')
                docs.append(
                    Document(
                        page_content=context,
                        metadata={
                            'query': query,
                            'collection_name': collection_name,
                        }
                    )
                )
            logger.info(f'Loading {filename}...')
            vector_store.add_documents(docs)


if __name__ == '__main__':
    populate_db = PopulateDatabase()
    populate_db.load_datasets()
