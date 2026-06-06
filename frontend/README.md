# Frontend

This folder contains the frontend application for the EAGL system.

- `src/frontend.py` defines the frontend router and template views.
- `src/main.py` is the FastAPI entrypoint for the frontend application.
- `src/static/` contains CSS and JS assets.
- `src/templates/` contains Jinja2 templates for UI pages.
- `requirements.txt` lists the dependencies required to run the frontend.

## Run instructions

From the `frontend` folder, install dependencies and start the server:

```bash
cd frontend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8001
```

If you run from the repository root instead, use:

```bash
python -m uvicorn frontend.src.main:app --reload --port 8001
```

Then open `http://localhost:8001` in your browser.
