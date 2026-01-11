

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

### Quick Start
```bash
# Ejecutar todos los tests
python manage.py test

# Ejecutar con coverage
coverage run --source='.' manage.py test
coverage report

# Generar reporte HTML
coverage html
# Abre htmlcov/index.html en tu navegador
```

### Tipos de Tests

#### Tests Unitarios
Los tests unitarios utilizan mocks para aislar componentes:
- `experiments/test_views.py` - Tests de API views
- `experiments/test_services.py` - Tests de servicios de ejecución
- `experiments/test_llm_providers.py` - Tests de providers LLM
- `experiments/tests.py` - Tests de modelos
- `llms/tests.py` - Tests de LLM y configuraciones
- `prompts/tests.py` - Tests de templates y prompts

#### Tests de Integración
Los tests de integración verifican flujos completos end-to-end:
- `experiments/test_integration.py` - Workflows completos de experimentos
- `llms/test_integration.py` - Workflows de LLM y configuraciones

### Ejecutar Tests Específicos
```bash
# Tests de una app
python manage.py test experiments

# Solo tests unitarios
python manage.py test experiments.test_views experiments.test_services llms.tests prompts.tests

# Solo tests de integración
python manage.py test experiments.test_integration llms.test_integration

# Un test específico
python manage.py test experiments.test_integration.ExperimentAPIIntegrationTests.test_complete_experiment_creation_workflow
```

### Code Coverage
```bash
# Generar reporte de coverage
coverage run --source='.' manage.py test
coverage report

# Generar reporte HTML
coverage html
# Abre htmlcov/index.html en tu navegador
```

Para más detalles, consulta [docs/COVERAGE_GUIDE.md](docs/COVERAGE_GUIDE.md) y [docs/TESTING_EXAMPLES.md](docs/TESTING_EXAMPLES.md)

## Project Structure
- `backend/` – Django project settings
- `experiments/`, `llms/`, `prompts/` – Main app modules

---
This is only the backend repository. For the frontend, see the corresponding frontend repository.