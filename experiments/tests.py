from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from .models import Experiment, Run, MobileApp, MobileAppRanked, RankingCriteria
from prompts.models import Template, SystemPrompt, UserPrompt, Feature
from llms.models import LLM, Configuration, ConfiguredModel


class ExperimentModelTests(TestCase):
    """Test cases for the Experiment model."""

    def setUp(self):
        """Set up test data."""
        # Create system and user prompts
        self.system_prompt = SystemPrompt.objects.create(
            text="You are a helpful assistant.",
            schema={"type": "json_object"}
        )
        self.user_prompt = UserPrompt.objects.create(
            text="Analyze the feature: {{ feature }}",
            k=5
        )
        
        # Create template
        self.template = Template.objects.create(
            name="Test Template",
            system_prompt=self.system_prompt,
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

    def test_create_experiment(self):
        """Test creating a basic experiment."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.template,
            num_runs=3
        )
        experiment.configured_models.add(self.configured_model)
        
        self.assertEqual(experiment.name, "Test Experiment")
        self.assertEqual(experiment.num_runs, 3)
        self.assertEqual(experiment.status, Experiment.Status.RUNNING)
        self.assertEqual(experiment.configured_models.count(), 1)
        self.assertIsNotNone(experiment.execution_date)

    def test_experiment_unique_name(self):
        """Test that experiment names must be unique."""
        Experiment.objects.create(
            name="Unique Experiment",
            prompt_template=self.template,
            num_runs=1
        )
        
        with self.assertRaises(IntegrityError):
            Experiment.objects.create(
                name="Unique Experiment",
                prompt_template=self.template,
                num_runs=1
            )

    def test_experiment_status_choices(self):
        """Test experiment status transitions."""
        experiment = Experiment.objects.create(
            name="Status Test",
            prompt_template=self.template,
            status=Experiment.Status.RUNNING
        )
        
        self.assertEqual(experiment.status, Experiment.Status.RUNNING)
        
        experiment.status = Experiment.Status.COMPLETED
        experiment.save()
        self.assertEqual(experiment.status, Experiment.Status.COMPLETED)
        
        experiment.status = Experiment.Status.FAILED
        experiment.save()
        self.assertEqual(experiment.status, Experiment.Status.FAILED)

    def test_experiment_str(self):
        """Test string representation of Experiment."""
        experiment = Experiment.objects.create(
            name="String Test Experiment",
            prompt_template=self.template
        )
        self.assertEqual(str(experiment), "String Test Experiment")


class RunModelTests(TestCase):
    """Test cases for the Run model."""

    def setUp(self):
        """Set up test data."""
        # Create basic dependencies
        self.system_prompt = SystemPrompt.objects.create(
            text="System",
            schema={"type": "json_object"}
        )
        self.user_prompt = UserPrompt.objects.create(
            text="User prompt for {{ feature }}",
            k=3
        )
        self.template = Template.objects.create(
            name="Template",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        self.feature = Feature.objects.create(
            name="Search",
            description="Search feature",
            user_prompt=self.user_prompt
        )
        
        self.config = Configuration.objects.create(name="Config")
        self.llm = LLM.objects.create(
            name="gpt-4",
            provider="OpenAI",
            API_key="key"
        )
        self.configured_model = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config,
            short_name="test-model"
        )
        
        self.experiment = Experiment.objects.create(
            name="Exp1",
            prompt_template=self.template,
            num_runs=2
        )
        self.experiment.configured_models.add(self.configured_model)

    def test_create_run(self):
        """Test creating a Run."""
        run = Run.objects.create(
            experiment=self.experiment,
            configured_model=self.configured_model,
            feature=self.feature,
            elapsed_time=1.5
        )
        
        self.assertEqual(run.experiment, self.experiment)
        self.assertEqual(run.configured_model, self.configured_model)
        self.assertEqual(run.feature, self.feature)
        self.assertEqual(run.elapsed_time, 1.5)

    def test_run_str(self):
        """Test string representation of Run."""
        run = Run.objects.create(
            experiment=self.experiment,
            configured_model=self.configured_model,
            feature=self.feature
        )
        self.assertIn("Exp1", str(run))

    def test_run_relationship_with_mobile_apps(self):
        """Test Run's relationship with MobileApps through MobileAppRanked."""
        run = Run.objects.create(
            experiment=self.experiment,
            configured_model=self.configured_model,
            feature=self.feature
        )
        
        app1 = MobileApp.objects.create(name="App 1", URL="http://app1.com")
        app2 = MobileApp.objects.create(name="App 2", URL="http://app2.com")
        
        MobileAppRanked.objects.create(run=run, mobile_app=app1, rank=1)
        MobileAppRanked.objects.create(run=run, mobile_app=app2, rank=2)
        
        self.assertEqual(run.apps.count(), 2)
        self.assertEqual(run.mobile_app_rankings.count(), 2)


class MobileAppModelTests(TestCase):
    """Test cases for the MobileApp model."""

    def test_create_mobile_app(self):
        """Test creating a MobileApp."""
        app = MobileApp.objects.create(
            name="TestApp",
            URL="https://testapp.com"
        )
        
        self.assertEqual(app.name, "TestApp")
        self.assertEqual(app.URL, "https://testapp.com")

    def test_mobile_app_str(self):
        """Test string representation of MobileApp."""
        app = MobileApp.objects.create(
            name="MyApp",
            URL="https://myapp.com"
        )
        self.assertEqual(str(app), "Mobile App: MyApp")


class MobileAppRankedModelTests(TestCase):
    """Test cases for the MobileAppRanked model."""

    def setUp(self):
        """Set up test data."""
        system_prompt = SystemPrompt.objects.create(
            text="System",
            schema={"type": "json_object"}
        )
        user_prompt = UserPrompt.objects.create(text="User", k=1)
        template = Template.objects.create(
            name="T",
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        feature = Feature.objects.create(
            name="F",
            user_prompt=user_prompt
        )
        
        config = Configuration.objects.create(name="C")
        llm = LLM.objects.create(name="gpt", provider="OpenAI", API_key="k")
        configured_model = ConfiguredModel.objects.create(
            llm=llm,
            configuration=config,
            short_name="test"
        )
        
        experiment = Experiment.objects.create(
            name="E",
            prompt_template=template
        )
        
        self.run = Run.objects.create(
            experiment=experiment,
            configured_model=configured_model,
            feature=feature
        )
        
        self.app1 = MobileApp.objects.create(name="App1", URL="http://app1.com")
        self.app2 = MobileApp.objects.create(name="App2", URL="http://app2.com")

    def test_create_mobile_app_ranked(self):
        """Test creating a MobileAppRanked."""
        ranked = MobileAppRanked.objects.create(
            run=self.run,
            mobile_app=self.app1,
            rank=1
        )
        
        self.assertEqual(ranked.rank, 1)
        self.assertEqual(ranked.mobile_app, self.app1)
        self.assertEqual(ranked.run, self.run)

    def test_unique_app_per_run_constraint(self):
        """Test that the unique constraint prevents duplicate (app, run, rank) combinations."""
        MobileAppRanked.objects.create(
            run=self.run,
            mobile_app=self.app1,
            rank=1
        )
        
        # Should raise IntegrityError when trying to create the same app with same rank in same run
        from django.db import transaction
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                MobileAppRanked.objects.create(
                    run=self.run,
                    mobile_app=self.app1,
                    rank=1  # Same rank - this should fail
                )

    def test_mobile_app_ranked_ordering(self):
        """Test that MobileAppRanked are ordered by rank."""
        MobileAppRanked.objects.create(run=self.run, mobile_app=self.app2, rank=2)
        MobileAppRanked.objects.create(run=self.run, mobile_app=self.app1, rank=1)
        
        rankings = self.run.mobile_app_rankings.all()
        self.assertEqual(rankings[0].rank, 1)
        self.assertEqual(rankings[1].rank, 2)

    def test_mobile_app_ranked_str(self):
        """Test string representation of MobileAppRanked."""
        ranked = MobileAppRanked.objects.create(
            run=self.run,
            mobile_app=self.app1,
            rank=3
        )
        self.assertIn("App1", str(ranked))
        self.assertIn("ranked 3", str(ranked))


class RankingCriteriaModelTests(TestCase):
    """Test cases for the RankingCriteria model."""

    def test_create_ranking_criteria(self):
        """Test creating a RankingCriteria."""
        criteria = RankingCriteria.objects.create(
            name="User Rating",
            description="Based on user reviews"
        )
        
        self.assertEqual(criteria.name, "User Rating")
        self.assertEqual(criteria.description, "Based on user reviews")

    def test_ranking_criteria_with_run(self):
        """Test linking RankingCriteria to a Run."""
        # Create dependencies
        system_prompt = SystemPrompt.objects.create(
            text="System",
            schema={"type": "json_object"}
        )
        user_prompt = UserPrompt.objects.create(text="User", k=1)
        template = Template.objects.create(
            name="T",
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        feature = Feature.objects.create(name="F", user_prompt=user_prompt)
        config = Configuration.objects.create(name="C")
        llm = LLM.objects.create(name="gpt", provider="OpenAI", API_key="k")
        configured_model = ConfiguredModel.objects.create(
            llm=llm,
            configuration=config,
            short_name="test"
        )
        experiment = Experiment.objects.create(name="E", prompt_template=template)
        
        run = Run.objects.create(
            experiment=experiment,
            configured_model=configured_model,
            feature=feature
        )
        
        criteria = RankingCriteria.objects.create(
            name="Performance",
            description="App performance",
            run=run
        )
        
        self.assertEqual(criteria.run, run)
        self.assertEqual(run.ranking_criteria.count(), 1)

    def test_ranking_criteria_str(self):
        """Test string representation of RankingCriteria."""
        criteria = RankingCriteria.objects.create(
            name="Popularity",
            description="Download count"
        )
        self.assertEqual(str(criteria), "Criterion: Popularity")
