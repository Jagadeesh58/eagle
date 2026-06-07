# Backend

This folder contains the backend API for the EAGL system.

- `backend.py` defines the API models and routes.
- `main.py` is the FastAPI entrypoint for the backend application.
- `eagle.py` contains the database access layer.
- `requirements.txt` lists the dependencies required to run the backend.

## Run instructions

From the `backend` folder, install dependencies and start the server:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open `http://localhost:8000/docs` to view the API documentation.
