import os
import time
import requests
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from llama_index.core import (
    Document, 
    VectorStoreIndex, 
    Settings
)
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.node_parser import (
    TokenTextSplitter,
    SentenceWindowNodeParser,
    SemanticSplitterNodeParser
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.schema import NodeWithScore
from llama_index.core.retrievers import VectorIndexRetriever
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class RetrievalResult:
    technique: str
    rank: int
    store_score: float
    cosine_sim: float
    chunk_len: int
    preview: str
    retrieval_time_ms: float


class ChunkingComparison:
    
    def __init__(self):
        self.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        Settings.embed_model = self.embed_model
        
        self.results = {}
        self.techniques = {}
        
    def download_tiny_shakespeare(self) -> str:
        url = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
        data_path = Path("tinyshakespeare.txt")
        
        if not data_path.exists():
            print("Downloading Tiny Shakespeare dataset...")
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                data_path.write_text(response.text, encoding="utf-8")
                print(f"Saved to {data_path.resolve()}")
            except Exception as e:
                print(f"Error downloading dataset: {e}")
                raise
        else:
            print(f"Using cached {data_path.resolve()}")
        
        raw_text = data_path.read_text(encoding="utf-8")
        print(f"Characters in corpus: {len(raw_text)}")
        print(f"First 400 chars:\n{raw_text[:400]}")
        return raw_text
    
    def setup_token_chunking(self, text: str) -> VectorStoreIndex:
        """Setup token-based chunking"""
        print("\n=== Setting up Token-based Chunking ===")
        
        token_splitter = TokenTextSplitter(
            chunk_size=512,  
            chunk_overlap=50 
        )
        
        document = Document(text=text)
        nodes = token_splitter.get_nodes_from_documents([document])
        
        print(f"Created {len(nodes)} chunks with token-based splitting")
        print(f"Average chunk length: {np.mean([len(node.text) for node in nodes]):.1f} characters")
        
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        
        self.techniques['token'] = {
            'index': index,
            'splitter': token_splitter,
            'nodes': nodes
        }
        
        return index
    
    def setup_semantic_chunking(self, text: str) -> VectorStoreIndex:
        """Setup semantic chunking"""
        print("\n=== Setting up Semantic Chunking ===")
        
        semantic_splitter = SemanticSplitterNodeParser(
            buffer_size=1,  
            breakpoint_percentile_threshold=95, 
            embed_model=self.embed_model
        )
        
        document = Document(text=text)
        nodes = semantic_splitter.get_nodes_from_documents([document])
        
        print(f"Created {len(nodes)} chunks with semantic splitting")
        print(f"Average chunk length: {np.mean([len(node.text) for node in nodes]):.1f} characters")
        
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        
        self.techniques['semantic'] = {
            'index': index,
            'splitter': semantic_splitter,
            'nodes': nodes
        }
        
        return index
    
    def setup_sentence_window_chunking(self, text: str) -> VectorStoreIndex:
        """Setup sentence-window chunking"""
        print("\n=== Setting up Sentence-Window Chunking ===")
        
        sentence_splitter = SentenceWindowNodeParser(
            window_size=3,  
            window_metadata_key="window",
            original_text_metadata_key="original_text"
        )
        
        document = Document(text=text)
        nodes = sentence_splitter.get_nodes_from_documents([document])
        
        print(f"Created {len(nodes)} chunks with sentence-window splitting")
        print(f"Average chunk length: {np.mean([len(node.text) for node in nodes]):.1f} characters")
        
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        
        self.techniques['sentence_window'] = {
            'index': index,
            'splitter': sentence_splitter,
            'nodes': nodes
        }
        
        return index
    
    def retrieve_and_analyze(self, technique: str, query: str, k: int = 5) -> List[RetrievalResult]:
        print(f"\n=== Retrieval Analysis for {technique.upper()} Chunking ===")
        
        index = self.techniques[technique]['index']
        nodes = self.techniques[technique]['nodes']
        
        retriever = VectorIndexRetriever(index=index, similarity_top_k=k)
        
        start_time = time.time()
        retrieved_nodes = retriever.retrieve(query)
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        query_embedding = self.embed_model.get_text_embedding(query)
        query_embedding = np.array(query_embedding).reshape(1, -1)
        
        print(f"Query embedding dimension: {query_embedding.shape[1]}")
        print(f"First 8 values of query embedding: {query_embedding[0][:8]}")
        
        results = []
        
        for rank, node in enumerate(retrieved_nodes, 1):
            doc_embedding = self.embed_model.get_text_embedding(node.text)
            doc_embedding = np.array(doc_embedding).reshape(1, -1)
            
            cosine_sim = cosine_similarity(query_embedding, doc_embedding)[0][0]
            
            store_score = getattr(node, 'score', 0.0)
            
            result = RetrievalResult(
                technique=technique,
                rank=rank,
                store_score=store_score,
                cosine_sim=cosine_sim,
                chunk_len=len(node.text),
                preview=node.text[:160] + "..." if len(node.text) > 160 else node.text,
                retrieval_time_ms=retrieval_time_ms
            )
            results.append(result)
        
        print(f"\nRetrieval Results for Query: '{query}'")
        print("-" * 120)
        print(f"{'Rank':<4} {'Store Score':<12} {'Cosine Sim':<12} {'Chunk Len':<10} {'Preview'}")
        print("-" * 120)
        
        for result in results:
            print(f"{result.rank:<4} {result.store_score:<12.4f} {result.cosine_sim:<12.4f} "
                  f"{result.chunk_len:<10} {result.preview}")
        
        print(f"\nQuery vector shape: {query_embedding.shape}")
        print(f"Document vectors shape: {len(retrieved_nodes)} x {query_embedding.shape[1]}")
        print(f"Retrieval time: {retrieval_time_ms:.2f} ms")
        
        return results
    
    def compare_techniques(self, queries: List[str]) -> Dict[str, Any]:
        print("\n" + "="*80)
        print("COMPREHENSIVE CHUNKING TECHNIQUES COMPARISON")
        print("="*80)
        
        comparison_results = {}
        
        for query in queries:
            print(f"\n{'='*60}")
            print(f"QUERY: {query}")
            print(f"{'='*60}")
            
            query_results = {}
            
            for technique in ['token', 'semantic', 'sentence_window']:
                results = self.retrieve_and_analyze(technique, query, k=5)
                query_results[technique] = results
                
                if technique not in comparison_results:
                    comparison_results[technique] = {
                        'total_chunks': len(self.techniques[technique]['nodes']),
                        'avg_chunk_length': np.mean([len(node.text) for node in self.techniques[technique]['nodes']]),
                        'query_results': {}
                    }
                
                comparison_results[technique]['query_results'][query] = {
                    'top1_cosine': max([r.cosine_sim for r in results]),
                    'mean_k_cosine': np.mean([r.cosine_sim for r in results]),
                    'retrieval_time_ms': results[0].retrieval_time_ms if results else 0
                }
        
        return comparison_results

def main():
    print("Starting LlamaIndex Chunking Techniques Comparison")
    print("=" * 60)
    
    comparison = ChunkingComparison()
    
    text = comparison.download_tiny_shakespeare()
    
    comparison.setup_token_chunking(text)
    comparison.setup_semantic_chunking(text)
    comparison.setup_sentence_window_chunking(text)
    
    queries = [
        "Who are the two feuding houses?",
        "Who is Romeo in love with?",
        "Which play contains the line 'To be, or not to be'?"
    ]
    
    comparison_results = comparison.compare_techniques(queries)
    

if __name__ == "__main__":
    main()
