# Backend

This folder contains the backend API for the EAGL system.

- `src/backend.py` defines the API models and routes.
- `src/main.py` is the FastAPI entrypoint for the backend application.
- `src/eagle.py` contains the database access layer.
- `src/get_users.py` contains additional user utilities.
- `requirements.txt` lists the dependencies required to run the backend.

## Run instructions

From the `backend` folder, install dependencies and start the server:

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

If you run from the repository root instead, use:

```bash
python -m uvicorn backend.src.main:app --reload --port 8000
```

Then open `http://localhost:8000/docs` to view the API documentation.
