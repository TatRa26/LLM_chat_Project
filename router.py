import re
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import os

class DatasetRouter:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.datasets = {}
        self.dataset_embeddings = {}
        self.load_datasets()
        
    def load_datasets(self):
        """Загрузка всех датасетов из директории data"""
        dataset_files = {
            "domru": "Дз1.txt",
            "faq": "FAQ.txt",
            "dataset3": "Дз3.txt",
            "dataset4": "Дз4.txt",
            "dataset5": "Дз5.txt"
        }
        
        for dataset_name, filename in dataset_files.items():
            file_path = os.path.join(self.data_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    chunks = content.split('\n\n')
                    
                dataset = []
                for chunk in chunks:
                    lines = chunk.split('\n')
                    if len(lines) >= 2:
                        query = re.sub("\*", "", lines[0])
                        text = re.sub("\n|\t", "", lines[1])
                        dataset.append({'query': query, 'chunk': text})
                
                self.datasets[dataset_name] = dataset
                
                # Создаем эмбеддинги для датасета
                dataset_texts = [item['chunk'] for item in dataset]
                self.dataset_embeddings[dataset_name] = self.model.encode(dataset_texts)
    
    def get_dataset_embedding(self, dataset_name: str) -> np.ndarray:
        """Получение эмбеддинга для названия датасета"""
        return self.model.encode([dataset_name])[0]
    
    def router(self, query: str, threshold: float = 0.5) -> Tuple[str, float]:
        """
        Маршрутизация запроса к наиболее подходящему датасету
        
        Args:
            query: Текст запроса
            threshold: Порог косинусного сходства
            
        Returns:
            Tuple[str, float]: (название датасета, косинусное сходство)
        """
        query_embedding = self.model.encode([query])[0]
        
        max_similarity = -1
        best_dataset = None
        
        for dataset_name in self.datasets.keys():
            dataset_embedding = self.get_dataset_embedding(dataset_name)
            similarity = np.dot(query_embedding, dataset_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(dataset_embedding)
            )
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_dataset = dataset_name
        
        if max_similarity >= threshold:
            return best_dataset, max_similarity
        return None, max_similarity
    
    def get_relevant_chunks(self, query: str, dataset_name: str, top_k: int = 3) -> List[Dict]:
        """
        Получение наиболее релевантных чанков из датасета
        
        Args:
            query: Текст запроса
            dataset_name: Название датасета
            top_k: Количество возвращаемых чанков
            
        Returns:
            List[Dict]: Список релевантных чанков
        """
        if dataset_name not in self.datasets:
            return []
            
        query_embedding = self.model.encode([query])[0]
        dataset_embeddings = self.dataset_embeddings[dataset_name]
        
        # Вычисляем косинусные сходства
        similarities = np.dot(dataset_embeddings, query_embedding) / (
            np.linalg.norm(dataset_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Получаем индексы top_k наиболее похожих чанков
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [self.datasets[dataset_name][i] for i in top_indices] 