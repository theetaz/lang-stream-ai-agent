# Lang Stream AI Agent

A FastAPI-based AI agent using LangGraph, PostgreSQL, and Redis, containerized with Docker.

## Prerequisites

- Docker
- Docker Compose

## Setup

1. Clone the repository:

   ```bash
     git clone <repository-url>
     cd project_root
   ```

2. Create a `.env` file based on the provided example.
3. Build and run the application:
   ```bash
   docker-compose up --build
   ```

## Usage

- Access the FastAPI app at `http://localhost:8000`.
- API documentation is available at `http://localhost:8000/docs`.
- Send a POST request to `/api/v1/agent` with a JSON body:
  ```json
  { "input": "Your query here" }
  ```

## Development

- FastAPI hot reloading is enabled. Changes to `app/` will reflect automatically.
- PostgreSQL and Redis data persist in Docker volumes.
