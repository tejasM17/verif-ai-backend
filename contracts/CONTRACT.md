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
  - Description: Check API health and current environment.
  - Response:
    ```json
    {
      "status": "healthy",
      "environment": "development"
    }
    ```

- **GET** `/`
  - Description: Welcome message and link to Swagger UI.
  - Response:
    ```json
    {
      "success": true,
      "message": "Welcome to VERIF-AI API",
      "docs": "/docs"
    }
    ```
