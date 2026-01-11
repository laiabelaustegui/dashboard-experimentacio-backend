"""
Test cases for experiment services.
"""
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
import json

from .services import ExperimentExecutionService
from .models import Experiment, Run, MobileApp, MobileAppRanked, RankingCriteria
from prompts.models import Template, SystemPrompt, UserPrompt, Feature
from llms.models import LLM, Configuration, ConfiguredModel


class ExperimentExecutionServiceTests(TestCase):
    """Test cases for ExperimentExecutionService."""

    def setUp(self):
        """Set up test data."""
        # Create prompts
        self.system_prompt = SystemPrompt.objects.create(
            text="You are a helpful assistant.",
            schema={"type": "json_object"}
        )
        self.user_prompt = UserPrompt.objects.create(
            text="Analyze feature: {{ feature }} with k={{ k }}",
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
        
        # Create experiment
        self.experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.template,
            num_runs=2
        )
        self.experiment.configured_models.add(self.configured_model)

    def test_execute_raises_error_when_no_configured_models(self):
        """Test that execute raises ValueError when no configured models exist."""
        experiment = Experiment.objects.create(
            name="Empty Experiment",
            prompt_template=self.template,
            num_runs=1
        )
        
        service = ExperimentExecutionService(experiment)
        
        with self.assertRaises(ValueError) as context:
            service.execute()
        
        self.assertIn("No configured models", str(context.exception))

    def test_execute_raises_error_when_no_features(self):
        """Test that execute raises ValueError when no features exist."""
        # Create a user prompt without features
        user_prompt_no_features = UserPrompt.objects.create(
            text="No features",
            k=1
        )
        # Create a new system prompt for this template
        system_prompt_no_features = SystemPrompt.objects.create(
            text="Another system prompt",
            schema={"type": "json_object"}
        )
        template_no_features = Template.objects.create(
            name="Template No Features",
            system_prompt=system_prompt_no_features,
            user_prompt=user_prompt_no_features
        )
        
        experiment = Experiment.objects.create(
            name="No Features Experiment",
            prompt_template=template_no_features,
            num_runs=1
        )
        experiment.configured_models.add(self.configured_model)
        
        service = ExperimentExecutionService(experiment)
        
        with self.assertRaises(ValueError) as context:
            service.execute()
        
        self.assertIn("No features", str(context.exception))

    @patch('experiments.services.LLMProviderFactory.create_provider')
    def test_execute_successful(self, mock_create_provider):
        """Test successful experiment execution."""
        # Mock the LLM provider
        mock_provider = Mock()
        mock_response = json.dumps({
            "a": ["App1", "App2", "App3"],
            "c": [
                {"n": "Performance", "d": "Speed and efficiency"},
                {"n": "Usability", "d": "User-friendly interface"}
            ]
        })
        mock_provider.create_completion.return_value = mock_response
        mock_create_provider.return_value = mock_provider
        
        service = ExperimentExecutionService(self.experiment)
        results = service.execute()
        
        # Verify execution
        self.assertEqual(len(results), 2)  # num_runs = 2
        self.assertEqual(Run.objects.filter(experiment=self.experiment).count(), 2)
        
        # Verify experiment status
        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.status, Experiment.Status.COMPLETED)
        
        # Verify run details
        run = Run.objects.filter(experiment=self.experiment).first()
        self.assertIsNotNone(run.elapsed_time)
        self.assertEqual(run.configured_model, self.configured_model)
        self.assertEqual(run.feature, self.feature)
        
        # Verify apps were created
        self.assertEqual(run.apps.count(), 3)
        self.assertEqual(MobileApp.objects.filter(name="App1").count(), 1)
        
        # Verify rankings
        self.assertEqual(run.mobile_app_rankings.count(), 3)
        first_ranking = run.mobile_app_rankings.first()
        self.assertEqual(first_ranking.rank, 1)
        
        # Verify criteria
        self.assertEqual(run.ranking_criteria.count(), 2)
        criteria = run.ranking_criteria.first()
        self.assertEqual(criteria.name, "Performance")

    @patch('experiments.services.LLMProviderFactory.create_provider')
    def test_execute_handles_llm_failure(self, mock_create_provider):
        """Test that execute handles LLM API failures correctly."""
        mock_provider = Mock()
        mock_provider.create_completion.side_effect = RuntimeError("API Error")
        mock_create_provider.return_value = mock_provider
        
        service = ExperimentExecutionService(self.experiment)
        
        with self.assertRaises(RuntimeError):
            service.execute()
        
        # Verify experiment status is FAILED
        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.status, Experiment.Status.FAILED)

    @patch('experiments.services.LLMProviderFactory.create_provider')
    def test_execute_handles_invalid_json_response(self, mock_create_provider):
        """Test that execute handles invalid JSON responses."""
        mock_provider = Mock()
        mock_provider.create_completion.return_value = "invalid json {{"
        mock_create_provider.return_value = mock_provider
        
        service = ExperimentExecutionService(self.experiment)
        
        with self.assertRaises(ValueError) as context:
            service.execute()
        
        self.assertIn("Invalid JSON", str(context.exception))
        
        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.status, Experiment.Status.FAILED)

    @patch('experiments.services.LLMProviderFactory.create_provider')
    def test_execute_with_top_p_configuration(self, mock_create_provider):
        """Test that top_p is correctly passed to the provider."""
        mock_provider = Mock()
        mock_provider.create_completion.return_value = json.dumps({
            "a": ["App1"],
            "c": []
        })
        mock_create_provider.return_value = mock_provider
        
        service = ExperimentExecutionService(self.experiment)
        service.execute()
        
        # Verify top_p was passed
        call_kwargs = mock_provider.create_completion.call_args[1]
        self.assertEqual(call_kwargs['top_p'], 0.9)
        self.assertEqual(call_kwargs['temperature'], 0.7)

    @patch('experiments.services.LLMProviderFactory.create_provider')
    def test_execute_without_top_p_when_default(self, mock_create_provider):
        """Test that top_p is not passed when it's the default value."""
        # Create config with default top_p
        config_default = Configuration.objects.create(
            name="Default Config",
            temperature=0.5,
            topP=1  # default value
        )
        configured_model_default = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=config_default,
            short_name="gpt-4-default"
        )
        
        experiment = Experiment.objects.create(
            name="Default Top P Experiment",
            prompt_template=self.template,
            num_runs=1
        )
        experiment.configured_models.add(configured_model_default)
        
        mock_provider = Mock()
        mock_provider.create_completion.return_value = json.dumps({
            "a": ["App1"],
            "c": []
        })
        mock_create_provider.return_value = mock_provider
        
        service = ExperimentExecutionService(experiment)
        service.execute()
        
        # Verify top_p was not passed (None)
        call_kwargs = mock_provider.create_completion.call_args[1]
        self.assertIsNone(call_kwargs['top_p'])

    @patch('experiments.services.LLMProviderFactory.create_provider')
    def test_create_ranked_apps_handles_duplicates(self, mock_create_provider):
        """Test that duplicate app names are handled correctly."""
        mock_provider = Mock()
        # Response with duplicate apps
        mock_provider.create_completion.return_value = json.dumps({
            "a": ["App1", "App2", "App1", "App3"],  # App1 is duplicated
            "c": []
        })
        mock_create_provider.return_value = mock_provider
        
        service = ExperimentExecutionService(self.experiment)
        service.execute()
        
        run = Run.objects.filter(experiment=self.experiment).first()
        
        # Should only have 3 unique apps
        self.assertEqual(run.apps.count(), 3)
        
        # Verify rankings are sequential
        rankings = run.mobile_app_rankings.all()
        ranks = [r.rank for r in rankings]
        self.assertEqual(ranks, [1, 2, 3])

    @patch('experiments.services.LLMProviderFactory.create_provider')
    def test_create_run_with_empty_apps_list(self, mock_create_provider):
        """Test handling of empty apps list."""
        mock_provider = Mock()
        mock_provider.create_completion.return_value = json.dumps({
            "a": [],
            "c": []
        })
        mock_create_provider.return_value = mock_provider
        
        service = ExperimentExecutionService(self.experiment)
        service.execute()
        
        run = Run.objects.filter(experiment=self.experiment).first()
        self.assertEqual(run.apps.count(), 0)

    @patch('experiments.services.LLMProviderFactory.create_provider')
    def test_create_ranking_criteria_without_optional_fields(self, mock_create_provider):
        """Test creating criteria with missing optional fields."""
        mock_provider = Mock()
        mock_provider.create_completion.return_value = json.dumps({
            "a": ["App1"],
            "c": [
                {"n": "Criterion1"},  # Missing description
                {}  # Missing both name and description
            ]
        })
        mock_create_provider.return_value = mock_provider
        
        service = ExperimentExecutionService(self.experiment)
        service.execute()
        
        run = Run.objects.filter(experiment=self.experiment).first()
        
        self.assertEqual(run.ranking_criteria.count(), 2)
        
        criteria = list(run.ranking_criteria.all())
        self.assertEqual(criteria[0].name, "Criterion1")
        self.assertEqual(criteria[0].description, "")
        self.assertEqual(criteria[1].name, "Unnamed Criterion")

    @patch('experiments.services.LLMProviderFactory.create_provider')
    def test_execute_multiple_configured_models(self, mock_create_provider):
        """Test execution with multiple configured models."""
        # Create another configured model
        config2 = Configuration.objects.create(
            name="Config 2",
            temperature=0.3
        )
        configured_model2 = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=config2,
            short_name="gpt-4-low-temp"
        )
        
        self.experiment.configured_models.add(configured_model2)
        
        mock_provider = Mock()
        mock_provider.create_completion.return_value = json.dumps({
            "a": ["App1"],
            "c": []
        })
        mock_create_provider.return_value = mock_provider
        
        service = ExperimentExecutionService(self.experiment)
        results = service.execute()
        
        # Should have runs for both models (2 models * 2 num_runs = 4)
        self.assertEqual(len(results), 4)
        self.assertEqual(Run.objects.filter(experiment=self.experiment).count(), 4)
        
        # Verify runs are distributed across models
        runs_model1 = Run.objects.filter(
            experiment=self.experiment,
            configured_model=self.configured_model
        ).count()
        runs_model2 = Run.objects.filter(
            experiment=self.experiment,
            configured_model=configured_model2
        ).count()
        
        self.assertEqual(runs_model1, 2)
        self.assertEqual(runs_model2, 2)
