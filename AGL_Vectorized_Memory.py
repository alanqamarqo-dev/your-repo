import numpy as np

class VectorizedMemoryManager:
    def __init__(self):
        self.memory_matrix = None  # Initialize an empty matrix for memory storage
        self.utility_scores = []  # Simulate a score column for rows that need to be removed
    
    def add_memory(self, vector):
        if self.memory_matrix is None:
            self.memory_matrix = np.array([vector])
            self.utility_scores.append(0)  # Assume all vectors are initially considered valid
        else:
            new_row = np.array(vector)
            self.memory_matrix = np.vstack((self.memory_matrix, new_row))
            self.utility_scores.append(0)  # Assume all vectors are initially considered valid
    
    def retrieve_similar(self, query_vector):
        if self.memory_matrix is None or self.memory_matrix.shape[0] == 0:
            raise ValueError("Memory matrix is empty. Please add memories first.")
        
        query_vector = np.array(query_vector)
        
        # Calculate cosine similarity
        dot_products = np.dot(self.memory_matrix, query_vector)
        norms = np.linalg.norm(self.memory_matrix, axis=1) * np.linalg.norm(query_vector)
        
        # Avoid division by zero
        norms[norms == 0] = 1e-10
        
        cosine_similarity = dot_products / norms
        
        # Find indices of the most similar rows
        top_k = min(5, len(cosine_similarity))
        similar_indices = np.argsort(cosine_similarity)[-top_k:][::-1]
        
        return self.memory_matrix[similar_indices], cosine_similarity[similar_indices]
    
    def optimize_storage(self):
        if not self.utility_scores:
            raise ValueError("Utility scores need to be calculated. Please add memories and calculate utility scores.")
        
        self.memory_matrix = np.delete(self.memory_matrix, [i for i, score in enumerate(self.utility_scores) if score <= 0], axis=0)
    
    def self_test(self):
        import time
        from scipy.spatial.distance import cosine
        
        test_vector = [1, 2, 3]
        query_vector = [4, 5, 6]
        
        # Test add_memory method
        self.add_memory(test_vector)
        assert np.array_equal(self.memory_matrix[0], np.array(test_vector))
        
        # Test retrieve_similar method
        similar_memories, cosine_scores = self.retrieve_similar(query_vector)
        assert len(similar_memories) >= 1  # We only added 1, so we expect at least 1 (or exactly 1)
        
        # Test optimize_storage method
        self.optimize_storage()
        
        print("Self-test successful.")