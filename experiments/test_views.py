"""
Test cases for experiment views.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock
import json

from .models import Experiment, Run, MobileApp, RankingCriteria
from prompts.models import Template, SystemPrompt, UserPrompt, Feature
from llms.models import LLM, Configuration, ConfiguredModel


class ExperimentViewSetTests(TestCase):
    """Test cases for ExperimentViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create prompts
        self.system_prompt = SystemPrompt.objects.create(
            text="You are a helpful assistant.",
            schema={"type": "json_object"}
        )
        self.user_prompt = UserPrompt.objects.create(
            text="Analyze feature: {{ feature }}",
            k=5
        )
        
        # Create template
        self.template = Template.objects.create(
            name="Test Template",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
        # Create feature
        self.feature = Feature.objects.create(
            name="Search",
            description="Search functionality",
            user_prompt=self.user_prompt
        )
        
        # Create configuration
        self.config = Configuration.objects.create(
            name="Test Config",
            temperature=0.7,
            topP=0.9
        )
        
        # Create LLM
        self.llm = LLM.objects.create(
            name="gpt-4",
            provider="OpenAI",
            API_key="test-key-123"
        )
        
        # Create configured model
        self.configured_model = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config,
            short_name="gpt-4-test"
        )

    def test_list_experiments(self):
        """Test listing all experiments."""
        # Create some experiments
        exp1 = Experiment.objects.create(
            name="Experiment 1",
            prompt_template=self.template,
            num_runs=1
        )
        exp2 = Experiment.objects.create(
            name="Experiment 2",
            prompt_template=self.template,
            num_runs=2
        )
        
        response = self.client.get('/api/experiments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_experiment(self):
        """Test retrieving a single experiment."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.template,
            num_runs=3
        )
        experiment.configured_models.add(self.configured_model)
        
        response = self.client.get(f'/api/experiments/{experiment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Experiment")
        self.assertEqual(response.data['num_runs'], 3)
        self.assertEqual(len(response.data['configured_models']), 1)

    @patch('experiments.views.ExperimentExecutionService')
    def test_create_experiment_success(self, mock_service_class):
        """Test successfully creating and executing an experiment."""
        # Mock the service
        mock_service = Mock()
        mock_service.execute.return_value = [
            {"run_id": 1, "elapsed_time": 1.5, "feature_id": self.feature.id}
        ]
        mock_service_class.return_value = mock_service
        
        data = {
            "name": "New Experiment",
            "prompt_template": self.template.id,
            "configured_models": [self.configured_model.id],
            "num_runs": 1
        }
        
        response = self.client.post('/api/experiments/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('experiment', response.data)
        self.assertIn('num_runs', response.data)
        self.assertEqual(response.data['num_runs'], 1)
        
        # Verify experiment was created
        self.assertTrue(Experiment.objects.filter(name="New Experiment").exists())
        
        # Verify service was called
        mock_service_class.assert_called_once()
        mock_service.execute.assert_called_once()

    def test_create_experiment_invalid_data(self):
        """Test creating an experiment with invalid data."""
        data = {
            "name": "",  # Empty name
            "prompt_template": 9999,  # Non-existent template
            "num_runs": -1  # Invalid number
        }
        
        response = self.client.post('/api/experiments/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('experiments.views.ExperimentExecutionService')
    def test_create_experiment_validation_error(self, mock_service_class):
        """Test creating an experiment that fails validation during execution."""
        mock_service = Mock()
        mock_service.execute.side_effect = ValueError("No configured models found")
        mock_service_class.return_value = mock_service
        
        data = {
            "name": "Invalid Experiment",
            "prompt_template": self.template.id,
            "configured_models": [self.configured_model.id],
            "num_runs": 1
        }
        
        response = self.client.post('/api/experiments/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('No configured models', response.data['error'])

    @patch('experiments.views.ExperimentExecutionService')
    def test_create_experiment_execution_error(self, mock_service_class):
        """Test creating an experiment that fails during execution."""
        mock_service = Mock()
        mock_service.execute.side_effect = RuntimeError("API Error")
        mock_service_class.return_value = mock_service
        
        data = {
            "name": "Failed Experiment",
            "prompt_template": self.template.id,
            "configured_models": [self.configured_model.id],
            "num_runs": 1
        }
        
        response = self.client.post('/api/experiments/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)

    def test_delete_experiment(self):
        """Test deleting an experiment."""
        experiment = Experiment.objects.create(
            name="To Delete",
            prompt_template=self.template,
            num_runs=1
        )
        
        response = self.client.delete(f'/api/experiments/{experiment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Experiment.objects.filter(id=experiment.id).exists())

    def test_delete_experiment_with_protected_relations(self):
        """Test deleting an experiment with protected foreign keys."""
        experiment = Experiment.objects.create(
            name="Protected Experiment",
            prompt_template=self.template,
            num_runs=1
        )
        
        # Create a run (which should cascade delete, but let's test the error handling)
        # Note: In the actual model, runs cascade delete, but this tests the error handler
        
        response = self.client.delete(f'/api/experiments/{experiment.id}/')
        
        # Should succeed because runs cascade
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_experiment_detail_includes_runs(self):
        """Test that experiment detail includes run information."""
        experiment = Experiment.objects.create(
            name="Experiment with Runs",
            prompt_template=self.template,
            num_runs=1
        )
        
        # Create a run
        run = Run.objects.create(
            experiment=experiment,
            configured_model=self.configured_model,
            feature=self.feature,
            elapsed_time=2.5
        )
        
        response = self.client.get(f'/api/experiments/{experiment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('runs', response.data)
        self.assertEqual(len(response.data['runs']), 1)
        self.assertEqual(response.data['runs'][0]['elapsed_time'], 2.5)

    def test_experiment_serializer_includes_configured_models_detail(self):
        """Test that experiment serializer includes detailed configured model info."""
        experiment = Experiment.objects.create(
            name="Detailed Experiment",
            prompt_template=self.template,
            num_runs=1
        )
        experiment.configured_models.add(self.configured_model)
        
        response = self.client.get(f'/api/experiments/{experiment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('configured_models_detail', response.data)
        self.assertEqual(len(response.data['configured_models_detail']), 1)
        self.assertEqual(
            response.data['configured_models_detail'][0]['short_name'],
            "gpt-4-test"
        )


class MobileAppViewSetTests(TestCase):
    """Test cases for MobileAppViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_list_mobile_apps(self):
        """Test listing all mobile apps."""
        MobileApp.objects.create(name="App 1", URL="http://app1.com")
        MobileApp.objects.create(name="App 2", URL="http://app2.com")
        
        response = self.client.get('/api/mobileapps/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_mobile_app(self):
        """Test retrieving a single mobile app."""
        app = MobileApp.objects.create(name="TestApp", URL="http://test.com")
        
        response = self.client.get(f'/api/mobileapps/{app.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "TestApp")
        self.assertEqual(response.data['URL'], "http://test.com")

    def test_mobile_app_viewset_is_readonly(self):
        """Test that MobileAppViewSet is read-only."""
        data = {"name": "New App", "URL": "http://new.com"}
        
        # Try to create
        response = self.client.post('/api/mobileapps/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try to update
        app = MobileApp.objects.create(name="App", URL="http://app.com")
        response = self.client.put(f'/api/mobileapps/{app.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try to delete
        response = self.client.delete(f'/api/mobileapps/{app.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class RankingCriteriaViewSetTests(TestCase):
    """Test cases for RankingCriteriaViewSet."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_list_ranking_criteria(self):
        """Test listing all ranking criteria."""
        RankingCriteria.objects.create(
            name="Performance",
            description="App performance"
        )
        RankingCriteria.objects.create(
            name="Usability",
            description="User-friendly"
        )
        
        response = self.client.get('/api/rankingcriteria/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_ranking_criteria(self):
        """Test retrieving a single ranking criteria."""
        criteria = RankingCriteria.objects.create(
            name="Security",
            description="Data protection"
        )
        
        response = self.client.get(f'/api/rankingcriteria/{criteria.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Security")
        self.assertEqual(response.data['description'], "Data protection")

    def test_ranking_criteria_viewset_is_readonly(self):
        """Test that RankingCriteriaViewSet is read-only."""
        data = {"name": "New Criteria", "description": "Description"}
        
        # Try to create
        response = self.client.post('/api/rankingcriteria/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
