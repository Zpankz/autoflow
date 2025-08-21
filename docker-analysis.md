# Docker Container Decomposition Analysis

## Current Container Architecture

### 1. **Backend Container** (`tidbai/backend:0.4.0`)
- **Base Image**: ghcr.io/astral-sh/uv:python3.11-bookworm-slim
- **Purpose**: FastAPI application with RAG capabilities
- **Dependencies**: supervisor, gcc, playwright, nltk
- **Exposed Ports**: 80 (FastAPI), 5555 (background/supervisord)
- **Volumes**: ./data:/shared/data
- **Enhancement Needs**: 
  - KG enhancement dependencies (cachetools)
  - Medical knowledge processing capabilities
  - Enhanced database migration support

### 2. **Frontend Container** (`tidbai/frontend:0.4.0`)
- **Base Image**: node:20-alpine
- **Purpose**: Next.js web application 
- **Build Process**: Multi-stage with pnpm
- **Exposed Ports**: 3000
- **Enhancement Needs**:
  - Medical UI components
  - Enhanced graph visualization
  - Critical care medicine content

### 3. **Supporting Services**
- **Redis**: redis:latest (caching and session storage)
- **Local Embedding/Reranker**: tidbai/local-embedding-reranker:v4-with-cache
- **Background Worker**: Same as backend with supervisord command

## Container Enhancement Strategy

### Phase 1: Backend Enhancement
- Add KG enhancement dependencies to backend Dockerfile
- Include medical knowledge processing capabilities
- Support enhanced database migrations
- Add environment configuration for medical domain

### Phase 2: Frontend Enhancement  
- Update frontend with medical knowledge components
- Enhance graph visualization for pharmacological relationships
- Replace placeholder content with critical care context

### Phase 3: Orchestration Enhancement
- Update docker-compose.yml with KG enhancement environment variables
- Add medical knowledge volume mounts
- Configure enhanced networking for parallel processing
