export * from './auth.types';
export * from './job.types';
export * from './skill.types';
export * from './profile.types';

export interface ApiResponse<T = any> {
    data?: T;
    message?: string;
    error?: string;
    status: number;
  }
  
  export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  }
  
  export interface ErrorResponse {
    detail: string;
    status?: number;
    type?: string;
  }
  
  export interface ValidationError {
    loc: string[];
    msg: string;
    type: string;
  }