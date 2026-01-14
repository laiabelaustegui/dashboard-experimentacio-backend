"""
Tests for the State pattern implementation in experiments.
"""
from django.test import TestCase
from experiments.models import Experiment
from experiments.experiment_states import (
    RunningState,
    CompletedState,
    FailedState,
    ExperimentStateContext
)
from prompts.models import Template as PromptTemplate, SystemPrompt, UserPrompt


class ExperimentStatePatternTestCase(TestCase):
    """Test the state pattern implementation for experiments."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create system and user prompts for the template
        self.system_prompt = SystemPrompt.objects.create(
            text="Test system prompt",
            schema={}
        )
        self.user_prompt = UserPrompt.objects.create(
            text="Test user prompt",
            k=5
        )
        self.prompt_template = PromptTemplate.objects.create(
            name="Test Template",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
    def test_experiment_initial_state_is_running(self):
        """Test that new experiments start in RUNNING state."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        self.assertEqual(experiment.status, Experiment.Status.RUNNING)
        state_context = experiment.get_state_context()
        self.assertIsInstance(state_context.current_state, RunningState)
    
    def test_running_experiment_can_complete(self):
        """Test that running experiments can transition to completed."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Should be able to complete
        self.assertTrue(experiment.get_state_context().current_state.can_complete())
        success = experiment.mark_as_completed()
        
        self.assertTrue(success)
        self.assertEqual(experiment.status, Experiment.Status.COMPLETED)
        self.assertIsInstance(experiment.get_state_context().current_state, CompletedState)
    
    def test_running_experiment_can_fail(self):
        """Test that running experiments can transition to failed."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Should be able to fail
        self.assertTrue(experiment.get_state_context().current_state.can_fail())
        success = experiment.mark_as_failed()
        
        self.assertTrue(success)
        self.assertEqual(experiment.status, Experiment.Status.FAILED)
        self.assertIsInstance(experiment.get_state_context().current_state, FailedState)
    
    def test_completed_experiment_cannot_execute(self):
        """Test that completed experiments cannot be re-executed."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Mark as completed
        experiment.mark_as_completed()
        
        # Should not be able to execute
        self.assertFalse(experiment.can_execute())
        success = experiment.mark_as_running()
        self.assertFalse(success)
        
        # Status should remain completed
        self.assertEqual(experiment.status, Experiment.Status.COMPLETED)
    
    def test_completed_experiment_cannot_fail(self):
        """Test that completed experiments cannot transition to failed."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Mark as completed
        experiment.mark_as_completed()
        
        # Should not be able to fail
        self.assertFalse(experiment.get_state_context().current_state.can_fail())
        success = experiment.mark_as_failed()
        self.assertFalse(success)
        
        # Status should remain completed
        self.assertEqual(experiment.status, Experiment.Status.COMPLETED)
    
    def test_failed_experiment_can_retry(self):
        """Test that failed experiments can be retried."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Mark as failed
        experiment.mark_as_failed()
        
        # Should be able to execute again
        self.assertTrue(experiment.can_execute())
        success = experiment.mark_as_running()
        self.assertTrue(success)
        
        # Status should be running again
        self.assertEqual(experiment.status, Experiment.Status.RUNNING)
        self.assertIsInstance(experiment.get_state_context().current_state, RunningState)
    
    def test_failed_experiment_cannot_complete_without_running(self):
        """Test that failed experiments cannot directly transition to completed."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Mark as failed
        experiment.mark_as_failed()
        
        # Should not be able to complete directly
        self.assertFalse(experiment.get_state_context().current_state.can_complete())
        success = experiment.mark_as_completed()
        self.assertFalse(success)
        
        # Status should remain failed
        self.assertEqual(experiment.status, Experiment.Status.FAILED)
    
    def test_state_context_persistence(self):
        """Test that state context is properly initialized from database status."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Manually set status to completed
        experiment.status = Experiment.Status.COMPLETED
        experiment.save()
        
        # Reload from database
        experiment = Experiment.objects.get(id=experiment.id)
        
        # State context should reflect the database status
        state_context = experiment.get_state_context()
        self.assertIsInstance(state_context.current_state, CompletedState)
        self.assertEqual(state_context.get_status_value(), 'completed')
    
    def test_running_state_cannot_execute(self):
        """Test that running experiments cannot be executed again."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Should not be able to execute a running experiment
        self.assertFalse(experiment.can_execute())
        success = experiment.mark_as_running()
        self.assertFalse(success)
        
        # Status should remain running
        self.assertEqual(experiment.status, Experiment.Status.RUNNING)
    
    def test_mark_methods_save_to_database(self):
        """Test that mark_* methods persist changes to the database."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Mark as completed with save=True (default)
        experiment.mark_as_completed()
        
        # Reload from database
        experiment_from_db = Experiment.objects.get(id=experiment.id)
        self.assertEqual(experiment_from_db.status, Experiment.Status.COMPLETED)
    
    def test_mark_methods_without_save(self):
        """Test that mark_* methods can skip database save."""
        experiment = Experiment.objects.create(
            name="Test Experiment",
            prompt_template=self.prompt_template,
            num_runs=1
        )
        
        # Mark as completed with save=False
        experiment.mark_as_completed(save=False)
        
        # In-memory status should be updated
        self.assertEqual(experiment.status, Experiment.Status.COMPLETED)
        
        # But database should still have RUNNING
        experiment_from_db = Experiment.objects.get(id=experiment.id)
        self.assertEqual(experiment_from_db.status, Experiment.Status.RUNNING)
