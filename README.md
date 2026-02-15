

# LLM-Powered Mobile App Recommender Experimentation Dashboard – Backend

This repository contains the backend for the "LLM-Powered Mobile App Recommender Experimentation Dashboard" project. It provides the core APIs, data models, and background processing for managing experiments, prompt templates, and LLM configurations.

## Features
- Experiment management with multiple LLM configurations
- LLM provider and configuration management
- Prompt template management with feature-based ranking
- RESTful API built with Django REST Framework
- Comprehensive test coverage (>90%)

## Getting Started

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd dashboard-experimentacio-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/api/`

## Running Tests

### Quick Start
```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report

# Generate HTML coverage report
coverage html
# Open htmlcov/index.html in your browser
```

### Test Types

#### Unit Tests
Unit tests use mocks to isolate components:
- `experiments/test_views.py` - API view tests
- `experiments/test_services.py` - Execution service tests
- `experiments/test_llm_providers.py` - LLM provider tests
- `experiments/tests.py` - Model tests
- `llms/tests.py` - LLM and configuration tests
- `prompts/tests.py` - Template and prompt tests

#### Integration Tests
Integration tests verify complete end-to-end workflows:
- `experiments/test_integration.py` - Complete experiment workflows
- `llms/test_integration.py` - LLM and configuration workflows

### Running Specific Tests
```bash
# Tests for a specific app
python manage.py test experiments

# Unit tests only
python manage.py test experiments.test_views experiments.test_services llms.tests prompts.tests

# Integration tests only
python manage.py test experiments.test_integration llms.test_integration

# Specific test case
python manage.py test experiments.test_integration.ExperimentAPIIntegrationTests.test_complete_experiment_creation_workflow

# Verbose output
python manage.py test --verbosity=2

# Stop on first failure
python manage.py test --failfast
```

### Code Coverage

The project maintains >90% code coverage. 

```bash
# Generate coverage report
coverage run --source='.' manage.py test
coverage report

# Generate interactive HTML report
coverage html
# Open htmlcov/index.html in your browser
```

**Current Coverage:** 90.34% (580 statements, 56 missing)

## Project Structure

```
dashboard-experimentacio-backend/
├── backend/              # Django project settings
│   ├── settings.py      # Main configuration
│   ├── urls.py          # Root URL configuration
│   └── celery.py        # Celery configuration (future use)
├── experiments/          # Experiments app
│   ├── models.py        # Experiment, Run, MobileApp models
│   ├── views.py         # API endpoints
│   ├── services.py      # Business logic
│   ├── serializers.py   # API serializers
│   └── llm_providers.py # LLM provider integrations
├── llms/                 # LLM management app
│   ├── models.py        # LLM, Configuration, ConfiguredModel
│   ├── views.py         # API endpoints
│   └── utils.py         # Encryption utilities
├── prompts/              # Prompt templates app
│   ├── models.py        # Template, SystemPrompt, UserPrompt, Feature
│   └── views.py         # API endpoints
├── requirements.txt      # Python dependencies
├── .coveragerc          # Coverage configuration
└── manage.py            # Django management script
```

## API Endpoints

### Experiments
- `GET /api/experiments/` - List all experiments
- `GET /api/experiments/{id}/` - Get experiment details
- `POST /api/experiments/` - Create and execute new experiment
- `DELETE /api/experiments/{id}/` - Delete experiment

### LLMs
- `GET /api/llms/` - List all LLM models
- `POST /api/llms/` - Register new LLM model
- `GET /api/llms/{id}/` - Get LLM details
- `PUT /api/llms/{id}/` - Update LLM configuration
- `DELETE /api/llms/{id}/` - Delete LLM model

### Configurations
- `GET /api/configurations/` - List all configurations
- `POST /api/configurations/` - Create new configuration
- `GET /api/configurations/{id}/` - Get configuration details
- `PUT /api/configurations/{id}/` - Update configuration
- `DELETE /api/configurations/{id}/` - Delete configuration

### Configured Models
- `GET /api/configured-models/` - List all configured models
- `POST /api/configured-models/` - Create new configured model
- `GET /api/configured-models/{id}/` - Get configured model details
- `DELETE /api/configured-models/{id}/` - Delete configured model

### Prompts
- `GET /api/templates/` - List all prompt templates
- `POST /api/templates/` - Create new template
- `GET /api/templates/{id}/` - Get template details

### Mobile Apps & Criteria (Read-only)
- `GET /api/mobileapps/` - List all mobile apps
- `GET /api/mobileapps/{id}/` - Get mobile app details
- `GET /api/rankingcriteria/` - List all ranking criteria
- `GET /api/rankingcriteria/{id}/` - Get criteria details

## Development

### Database
The project uses SQLite for development. The database file is `db.sqlite3` (not tracked in git).

### Migrations
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Django Admin
Create a superuser to access the admin panel:
```bash
python manage.py createsuperuser
```
Then visit `http://localhost:8000/admin/`

### Environment Variables
Create a `.env` file for sensitive configuration:
```bash
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Testing Best Practices

1. **Run tests frequently**: Before each commit
2. **Maintain coverage**: Keep coverage above 90%
3. **Write both unit and integration tests**: Unit tests for logic, integration tests for workflows
4. **Use meaningful test names**: Describe what is being tested
5. **Keep tests isolated**: Each test should be independent

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `python manage.py test`
4. Check coverage: `coverage run --source='.' manage.py test && coverage report`
5. Submit a pull request

## Technology Stack

- **Framework**: Django 5.2.7
- **API**: Django REST Framework 3.16.1
- **Database**: PostgreSQL
- **Task Queue**: Celery 5.6.0 (configured but not in use)
- **LLM Integration**: OpenAI SDK 2.6.1
- **Testing**: Django TestCase, Coverage.py 7.6.10
- **Security**: Cryptography 46.0.3 (for API key encryption)

## Related Repositories

This is the backend repository. For the frontend application, see:
- [dashboard-experimentacio-frontend](../dashboard-experimentacio-frontend) - Next.js frontend

## License

[Add license information here]

## Contact

[Add contact information here]
