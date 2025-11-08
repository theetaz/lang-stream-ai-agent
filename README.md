# LangGraph AI Agent

A full-stack AI agent application built with LangGraph, featuring a FastAPI backend and Next.js frontend with shadcn/ui components. Everything is containerized with Docker for easy deployment.

## Tech Stack

### Frontend

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **shadcn/ui** - Beautiful and accessible UI components
- **Tailwind CSS** - Utility-first styling

### Backend

- **FastAPI** - Modern Python web framework
- **LangGraph** - AI agent orchestration
- **PostgreSQL 16** - Relational database
- **Redis 7** - Caching and message broker

## Project Structure

```
lang-stream-ai-agent/
├── frontend/              # Next.js frontend application
│   ├── app/              # Next.js app directory
│   ├── lib/              # Utility functions and API client
│   └── components/       # React components
├── backend/              # FastAPI backend application
│   ├── agents/           # LangGraph agent implementations
│   ├── api/              # API routes
│   ├── database/         # Database client
│   └── redis/            # Redis client
├── docker/               # Dockerfile configurations
│   ├── frontend/         # Frontend Dockerfile
│   └── fastapi/          # Backend Dockerfile
└── docker-compose.yml    # Docker Compose configuration
```

## Prerequisites

- Docker
- Docker Compose

## Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd lang-stream-ai-agent
   ```

2. Create a `.env` file in the root directory:

   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=aiagent
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   REDIS_HOST=redis
   REDIS_PORT=6379
   ```

3. Build and run the entire stack:
   ```bash
   docker-compose up --build
   ```

## Usage

### Access the Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6379

### API Example

Send a POST request to `/api/v1/agent` with a JSON body:

```json
{
  "input": "Your query here"
}
```

## Development

### Frontend Development

The frontend supports hot reloading. Changes to files in `frontend/` will reflect automatically.

To run the frontend locally (outside Docker):

```bash
cd frontend
npm install
npm run dev
```

### Backend Development

The backend has hot reloading enabled. Changes to files in `backend/` will reflect automatically when running in Docker.

To run the backend locally (outside Docker):

1. **Create and activate a virtual environment** (recommended):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies**:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Run the backend**:

```bash
uvicorn main:app --reload
```

4. **Run the tests**:

```bash
pytest tests/

# to run the tests for the auth module
pytest tests/unit/test_auth_*.py -v
```

The virtual environment (`.venv`) is already in `.gitignore` and should be created in the `backend/` directory.

### Adding shadcn/ui Components

```bash
cd frontend
npx shadcn@latest add <component-name>
```

## Docker Services

- **frontend**: Next.js application (port 3000)
- **fastapi**: Python FastAPI backend (port 8000)
- **postgres**: PostgreSQL database (port 5433)
- **redis**: Redis cache (port 6379)

All services are connected via a custom Docker network (`ai-agent-network`).

## Data Persistence

PostgreSQL and Redis data persist in Docker volumes:

- `postgres_data`: Database files
- `redis_data`: Redis data

## Environment Variables

### Frontend

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

### Backend

- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: Database name
- `POSTGRES_HOST`: Database host
- `POSTGRES_PORT`: Database port
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port

## License

MIT
