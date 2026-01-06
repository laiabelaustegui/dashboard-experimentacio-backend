

# LLM-Powered Mobile App Recommender Experimentation Dashboard – Backend

This repository contains the backend for the "LLM-Powered Mobile App Recommender Experimentation Dashboard" project. It provides the core APIs, data models, and background processing for managing experiments, prompt templates, and LLM configurations.

## Features
- Experiment management
- LLM provider and configuration management
- Prompt template management
- RESTful API (Django)

## Getting Started
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run migrations:
   ```bash
   python manage.py migrate
   ```
3. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Running Tests
```bash
python manage.py test
```

## Project Structure
- `backend/` – Django project settings
- `experiments/`, `llms/`, `prompts/` – Main app modules

---
This is only the backend repository. For the frontend, see the corresponding frontend repository.