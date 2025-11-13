import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

export interface Document {
  id: string
  name: string
  type: 'pdf' | 'docx' | 'txt' | 'md'
  status: 'pending' | 'processing' | 'indexed' | 'failed'
  file_size: number
  chunks_count: number
  created_at: string
  error_message?: string
}

export interface DocumentsResponse {
  documents: Document[]
  total: number
}

export interface CollectionStats {
  collection_name: string
  total_chunks: number
  embedding_dimension: number
}

export const documentsApi = {
  /**
   * Upload a document
   */
  async uploadDocument(file: File): Promise<{ id: string; message: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(`${API_URL}/documents/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    return response.data
  },

  /**
   * Get all documents
   */
  async getDocuments(): Promise<DocumentsResponse> {
    const response = await axios.get(`${API_URL}/documents/`)
    return response.data
  },

  /**
   * Get single document
   */
  async getDocument(id: string): Promise<Document> {
    const response = await axios.get(`${API_URL}/documents/${id}`)
    return response.data
  },

  /**
   * Delete document
   */
  async deleteDocument(id: string): Promise<{ message: string }> {
    const response = await axios.delete(`${API_URL}/documents/${id}`)
    return response.data
  },

  /**
   * Reindex document
   */
  async reindexDocument(id: string): Promise<{ message: string }> {
    const response = await axios.post(`${API_URL}/documents/${id}/reindex`)
    return response.data
  },

  /**
   * Get collection statistics
   */
  async getCollectionStats(): Promise<CollectionStats> {
    const response = await axios.get(`${API_URL}/documents/stats/collection`)
    return response.data
  },
}
