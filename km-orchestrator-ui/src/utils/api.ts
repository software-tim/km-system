const API_BASE = 'https://km-orchestrator.azurewebsites.net';

export interface ApiResponse<T = any> {
  status: string;
  data?: T;
  message?: string;
  error?: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = ${'$'}{this.baseUrl}{endpoint};
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(HTTP error! status: {response.status});
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Search methods
  async search(query: string, limit: number = 10) {
    return this.request('/api/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
  }

  // Chat methods
  async chat(message: string) {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  // Upload methods
  async uploadDocument(document: any) {
    return this.request('/api/upload', {
      method: 'POST',
      body: JSON.stringify(document),
    });
  }

  // Health methods
  async getHealth() {
    return this.request('/api/simple-test');
  }

  async getServiceStatus() {
    return this.request('/services/status');
  }

  // Analytics methods
  async getDocumentStats() {
    return this.request('/proxy/docs-stats');
  }
}

export const apiClient = new ApiClient();
