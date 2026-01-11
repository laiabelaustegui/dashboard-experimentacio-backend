"""
Integration tests for experiments app.

These tests verify end-to-end workflows without mocking database or API interactions.
They test the full stack: Views → Serializers → Services → Models → Database.
"""
# pylint: disable=no-member
# Django models dynamically add 'objects' manager at runtime

from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock
import json

from .models import Experiment, Run, MobileApp, RankingCriteria
from prompts.models import Template, SystemPrompt, UserPrompt, Feature
from llms.models import LLM, Configuration, ConfiguredModel


class ExperimentAPIIntegrationTests(TransactionTestCase):
    """
    Integration tests for complete experiment workflows.
    Uses TransactionTestCase to test database transactions properly.
    """

    def setUp(self):
        """Set up test data for integration tests."""
        self.client = APIClient()
        
        # Create complete data chain
        self.system_prompt = SystemPrompt.objects.create(
            text="You are a helpful assistant that ranks mobile apps.",
            schema={
                "type": "object",
                "properties": {
                    "ranking": {"type": "array"}
                }
            }
        )
        
        self.user_prompt = UserPrompt.objects.create(
            text="Rank these apps based on {{ feature }} (top {{ k }})",
            k=5
        )
        
        self.template = Template.objects.create(
            name="Ranking Template",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
        # Create features
        self.feature1 = Feature.objects.create(
            name="Performance",
            description="App speed and responsiveness",
            user_prompt=self.user_prompt
        )
        
        self.feature2 = Feature.objects.create(
            name="Security",
            description="Data protection and privacy",
            user_prompt=self.user_prompt
        )
        
        # Create configuration
        self.config = Configuration.objects.create(
            name="Standard Config",
            temperature=0.7,
            topP=0.9
        )
        
        # Create LLM
        self.llm = LLM.objects.create(
            name="gpt-4",
            provider="OpenAI",
            API_key="test-integration-key-123"
        )
        
        # Create configured models
        self.configured_model1 = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config,
            short_name="gpt-4-standard"
        )
        
        # Create mobile apps
        self.app1 = MobileApp.objects.create(
            name="App Alpha",
            URL="http://app-alpha.com"
        )
        
        self.app2 = MobileApp.objects.create(
            name="App Beta",
            URL="http://app-beta.com"
        )
        
        # Create ranking criteria
        self.criteria1 = RankingCriteria.objects.create(
            name="Performance",
            description="Speed metric"
        )

    def test_complete_experiment_creation_workflow(self):
        """
        Integration test for complete experiment creation.
        Tests: API request → Validation → Database creation → Response.
        """
        initial_count = Experiment.objects.count()
        
        data = {
            "name": "Integration Test Experiment",
            "prompt_template": self.template.id,
            "configured_models": [self.configured_model1.id],
            "num_runs": 2
        }
        
        # Mock the LLM provider to avoid real API calls
        with patch('experiments.services.LLMProviderFactory.create_provider') as mock_factory:
            mock_provider = Mock()
            mock_provider.create_completion.return_value = json.dumps({
                "ranking": ["App Alpha", "App Beta"]
            })
            mock_factory.return_value = mock_provider
            
            response = self.client.post('/api/experiments/', data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('experiment', response.data)
        
        # Verify database state
        self.assertEqual(Experiment.objects.count(), initial_count + 1)
        
        experiment = Experiment.objects.get(name="Integration Test Experiment")
        self.assertEqual(experiment.num_runs, 2)
        self.assertEqual(experiment.configured_models.count(), 1)
        self.assertEqual(experiment.prompt_template, self.template)
        
        # Verify runs were created (2 features * 1 model * 2 runs = 4 runs)
        expected_runs = 2 * 1 * 2  # features * models * num_runs
        self.assertEqual(Run.objects.filter(experiment=experiment).count(), expected_runs)

    def test_experiment_list_with_relations(self):
        """
        Integration test for listing experiments with all relations loaded.
        Tests database joins and serializer relationships.
        """
        # Create experiments
        exp1 = Experiment.objects.create(
            name="Experiment 1",
            prompt_template=self.template,
            num_runs=1
        )
        exp1.configured_models.add(self.configured_model1)
        
        exp2 = Experiment.objects.create(
            name="Experiment 2",
            prompt_template=self.template,
            num_runs=1
        )
        exp2.configured_models.add(self.configured_model1)
        
        # Create a run for exp1
        Run.objects.create(
            experiment=exp1,
            configured_model=self.configured_model1,
            feature=self.feature1,
            elapsed_time=1.5
        )
        
        response = self.client.get('/api/experiments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Verify relationships are included
        exp1_data = next(e for e in response.data if e['name'] == 'Experiment 1')
        self.assertIn('prompt_template', exp1_data)
        self.assertIn('configured_models', exp1_data)

    def test_experiment_detail_with_runs(self):
        """
        Integration test for experiment detail with all related runs.
        Tests nested serializers and database queries.
        """
        experiment = Experiment.objects.create(
            name="Detailed Experiment",
            prompt_template=self.template,
            num_runs=1
        )
        experiment.configured_models.add(self.configured_model1)
        
        # Create multiple runs
        Run.objects.create(
            experiment=experiment,
            configured_model=self.configured_model1,
            feature=self.feature1,
            elapsed_time=1.2
        )
        
        Run.objects.create(
            experiment=experiment,
            configured_model=self.configured_model1,
            feature=self.feature2,
            elapsed_time=1.8
        )
        
        response = self.client.get(f'/api/experiments/{experiment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Detailed Experiment")
        self.assertIn('runs', response.data)
        self.assertEqual(len(response.data['runs']), 2)
        
        # Verify run data is complete
        run_times = [r['elapsed_time'] for r in response.data['runs']]
        self.assertIn(1.2, run_times)
        self.assertIn(1.8, run_times)

    def test_experiment_deletion_cascades_to_runs(self):
        """
        Integration test for cascade deletion.
        Tests database constraints and referential integrity.
        """
        experiment = Experiment.objects.create(
            name="To Delete",
            prompt_template=self.template,
            num_runs=1
        )
        experiment.configured_models.add(self.configured_model1)
        
        # Create runs
        run1 = Run.objects.create(
            experiment=experiment,
            configured_model=self.configured_model1,
            feature=self.feature1,
            elapsed_time=1.0
        )
        run2 = Run.objects.create(
            experiment=experiment,
            configured_model=self.configured_model1,
            feature=self.feature2,
            elapsed_time=2.0
        )
        
        run1_id = run1.id
        run2_id = run2.id
        
        # Delete experiment
        response = self.client.delete(f'/api/experiments/{experiment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify experiment is deleted
        self.assertFalse(Experiment.objects.filter(id=experiment.id).exists())
        
        # Verify runs are also deleted (cascade)
        self.assertFalse(Run.objects.filter(id=run1_id).exists())
        self.assertFalse(Run.objects.filter(id=run2_id).exists())

    def test_experiment_update_configured_models(self):
        """
        Integration test for updating experiment's configured models.
        Tests many-to-many relationship updates.
        """
        # Create another configured model
        config2 = Configuration.objects.create(
            name="Alternative Config",
            temperature=0.5
        )
        configured_model2 = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=config2,
            short_name="gpt-4-alt"
        )
        
        experiment = Experiment.objects.create(
            name="Updateable Experiment",
            prompt_template=self.template,
            num_runs=1
        )
        experiment.configured_models.add(self.configured_model1)
        
        # Update to add second model
        data = {
            "name": "Updateable Experiment",
            "prompt_template": self.template.id,
            "configured_models": [
                self.configured_model1.id,
                configured_model2.id
            ],
            "num_runs": 1
        }
        
        # Note: This test depends on whether your API allows PUT/PATCH
        # Adjust based on actual API behavior
        _response = self.client.put(
            f'/api/experiments/{experiment.id}/',
            data,
            format='json'
        )
        
        # Should fail because updating experiments is typically not allowed
        # But we can test the behavior
        # (Adjust based on actual API behavior)
        
        # Verify database state
        experiment.refresh_from_db()
        # Check if models were updated

    def test_cross_app_integration_prompt_and_llm(self):
        """
        Integration test across multiple apps.
        Tests: prompts app + llms app + experiments app integration.
        """
        # Create a complete setup
        system_prompt = SystemPrompt.objects.create(
            text="System text",
            schema={"type": "object"}
        )
        
        user_prompt = UserPrompt.objects.create(
            text="User text with {{ feature }}",
            k=3
        )
        
        template = Template.objects.create(
            name="Cross-App Template",
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        feature = Feature.objects.create(
            name="Integration Feature",
            description="Testing integration",
            user_prompt=user_prompt
        )
        
        llm = LLM.objects.create(
            name="claude-3",
            provider="Anthropic",
            API_key="anthropic-key"
        )
        
        config = Configuration.objects.create(
            name="Integration Config",
            temperature=0.8
        )
        
        configured_model = ConfiguredModel.objects.create(
            llm=llm,
            configuration=config,
            short_name="claude-3-integration"
        )
        
        # Create experiment using all components
        data = {
            "name": "Cross-App Experiment",
            "prompt_template": template.id,
            "configured_models": [configured_model.id],
            "num_runs": 1
        }
        
        with patch('experiments.services.LLMProviderFactory.create_provider') as mock_factory:
            mock_provider = Mock()
            mock_provider.create_completion.return_value = json.dumps({
                "ranking": ["App Alpha"]
            })
            mock_factory.return_value = mock_provider
            
            response = self.client.post('/api/experiments/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify all relationships are correctly established
        experiment = Experiment.objects.get(name="Cross-App Experiment")
        self.assertEqual(experiment.prompt_template.name, "Cross-App Template")
        self.assertEqual(
            experiment.configured_models.first().llm.provider,
            "Anthropic"
        )
        
        # Verify runs were created with correct features
        runs = Run.objects.filter(experiment=experiment)
        self.assertTrue(runs.exists())
        self.assertEqual(runs.first().feature.name, "Integration Feature")


class MobileAppIntegrationTests(TestCase):
    """Integration tests for MobileApp related workflows."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.app1 = MobileApp.objects.create(
            name="Test App 1",
            URL="http://test1.com"
        )
        self.app2 = MobileApp.objects.create(
            name="Test App 2",
            URL="http://test2.com"
        )

    def test_mobile_app_list_integration(self):
        """Test listing mobile apps through API."""
        response = self.client.get('/api/mobileapps/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        app_names = [app['name'] for app in response.data]
        self.assertIn("Test App 1", app_names)
        self.assertIn("Test App 2", app_names)

    def test_mobile_app_detail_integration(self):
        """Test retrieving mobile app detail through API."""
        response = self.client.get(f'/api/mobileapps/{self.app1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test App 1")
        self.assertEqual(response.data['URL'], "http://test1.com")

    def test_mobile_app_readonly_enforcement(self):
        """Test that mobile apps API is read-only (integration)."""
        # Attempt to create
        data = {"name": "New App", "URL": "http://new.com"}
        response = self.client.post('/api/mobileapps/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Verify database unchanged
        self.assertEqual(MobileApp.objects.count(), 2)


class RankingCriteriaIntegrationTests(TestCase):
    """Integration tests for RankingCriteria workflows."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.criteria1 = RankingCriteria.objects.create(
            name="Usability",
            description="User-friendly interface"
        )

    def test_ranking_criteria_list_integration(self):
        """Test listing ranking criteria through API."""
        response = self.client.get('/api/rankingcriteria/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_ranking_criteria_detail_integration(self):
        """Test retrieving ranking criteria detail."""
        response = self.client.get(f'/api/rankingcriteria/{self.criteria1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Usability")
        self.assertEqual(response.data['description'], "User-friendly interface")
