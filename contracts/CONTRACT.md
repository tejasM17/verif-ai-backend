# VERIF-AI API Contract
> Auto-updated by agent after every endpoint change.
> Backend: tejasM17/verif-ai-backend
> Frontend: SharathKumar-M/verif-ai-frontend

## Base URLs
- Local: http://localhost:8000
- Production: https://verif-ai-backend.onrender.com

## Endpoints

### System
- **GET** `/health`
  - Description: Check API health and connectivity to external services.
  - Response:
    ```json
    {
      "status": "healthy",
      "mongodb": "connected",
      "firebase": "connected"
    }
    ```

- **GET** `/`
  - Description: Welcome message and link to Swagger UI.
  - Response:
    ```json
    {
      "message": "VERIF-AI API",
      "docs": "/docs",
      "version": "1.0.0"
    }
    ```
