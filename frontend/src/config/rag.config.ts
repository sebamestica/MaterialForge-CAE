export const ragConfig = {
  // Document ingestion settings
  ingest: {
    supportedExtensions: ['.pdf', '.md', '.txt', '.json'],
    targetDirectories: ['/data/docs', '/data/processed', '/ia_agent/literature/docs'],
  },

  // Parsing & chunking parameters
  chunking: {
    chunkSize: 1000,      // characters
    chunkOverlap: 150,    // characters
    parser: 'markdown-aware',
  },

  // Retrieval parameters
  retrieval: {
    topK: 4,              // Number of documents retrieved for LLM context
    similarityThreshold: 0.35, // Similarity cutoff
    reranker: {
      enabled: false,
      model: 'bge-reranker-large',
    }
  },

  // Vector DB file target paths
  vectorStore: {
    outputDirectory: 'data/rag_index',
    indexFile: 'vector_store.json',
    manifestFile: 'index_manifest.json',
  }
};
