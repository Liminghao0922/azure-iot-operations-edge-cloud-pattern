# Application Example

This directory contains example application code for this pattern.

## Structure

- `src/` - Application source code
- `tests/` - Integration and unit tests

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python -m app.main

# Run tests
pytest tests/
```

## Docker

```bash
# Build image
docker build -t myapp:latest .

# Run container
docker run -p 8000:8000 myapp:latest
```

## Deployment

See `../deployment/` for Kubernetes deployment manifests.
