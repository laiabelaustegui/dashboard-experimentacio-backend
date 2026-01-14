"""
State pattern implementation for Experiment status.
This module defines the state classes and transitions for experiment execution.
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ExperimentState(ABC):
    """Abstract base class for experiment states."""
    
    @abstractmethod
    def get_status_value(self) -> str:
        """Return the string value of the status."""
        pass
    
    @abstractmethod
    def can_execute(self) -> bool:
        """Check if the experiment can be executed in this state."""
        pass
    
    @abstractmethod
    def can_complete(self) -> bool:
        """Check if the experiment can transition to completed state."""
        pass
    
    @abstractmethod
    def can_fail(self) -> bool:
        """Check if the experiment can transition to failed state."""
        pass
    
    def on_enter(self, experiment) -> None:
        """Hook called when entering this state."""
        logger.info(f"Experiment {experiment.id} entering {self.__class__.__name__}")
    
    def on_exit(self, experiment) -> None:
        """Hook called when exiting this state."""
        logger.info(f"Experiment {experiment.id} exiting {self.__class__.__name__}")


class RunningState(ExperimentState):
    """State representing a running experiment."""
    
    def get_status_value(self) -> str:
        return 'running'
    
    def can_execute(self) -> bool:
        return False  # Cannot execute an already running experiment
    
    def can_complete(self) -> bool:
        return True  # Running experiments can complete
    
    def can_fail(self) -> bool:
        return True  # Running experiments can fail
    
    def on_enter(self, experiment) -> None:
        super().on_enter(experiment)
        logger.info(f"Experiment {experiment.id} '{experiment.name}' has started running")


class CompletedState(ExperimentState):
    """State representing a completed experiment."""
    
    def get_status_value(self) -> str:
        return 'completed'
    
    def can_execute(self) -> bool:
        return False  # Cannot execute a completed experiment
    
    def can_complete(self) -> bool:
        return False  # Already completed
    
    def can_fail(self) -> bool:
        return False  # Cannot fail a completed experiment
    
    def on_enter(self, experiment) -> None:
        super().on_enter(experiment)
        logger.info(f"Experiment {experiment.id} '{experiment.name}' has completed successfully")


class FailedState(ExperimentState):
    """State representing a failed experiment."""
    
    def get_status_value(self) -> str:
        return 'failed'
    
    def can_execute(self) -> bool:
        return True  # Can retry a failed experiment
    
    def can_complete(self) -> bool:
        return False  # Cannot complete a failed experiment without re-running
    
    def can_fail(self) -> bool:
        return False  # Already failed
    
    def on_enter(self, experiment) -> None:
        super().on_enter(experiment)
        logger.error(f"Experiment {experiment.id} '{experiment.name}' has failed")


class ExperimentStateContext:
    """
    Context class that manages experiment state transitions.
    This class is used by the Experiment model to manage its state.
    """
    
    def __init__(self, experiment):
        self.experiment = experiment
        self._state: Optional[ExperimentState] = None
        self._initialize_state()
    
    def _initialize_state(self) -> None:
        """Initialize the state based on the current status value."""
        status_value = self.experiment.status
        self._state = self._create_state_from_value(status_value)
    
    def _create_state_from_value(self, status_value: str) -> ExperimentState:
        """Create a state object from the status string value."""
        state_map = {
            'running': RunningState(),
            'completed': CompletedState(),
            'failed': FailedState(),
        }
        state = state_map.get(status_value)
        if state is None:
            raise ValueError(f"Unknown status value: {status_value}")
        return state
    
    @property
    def current_state(self) -> ExperimentState:
        """Get the current state."""
        return self._state
    
    def get_status_value(self) -> str:
        """Get the current status value."""
        return self._state.get_status_value()
    
    def can_execute(self) -> bool:
        """Check if the experiment can be executed."""
        return self._state.can_execute()
    
    def transition_to_running(self) -> bool:
        """
        Transition to running state.
        Returns True if transition was successful, False otherwise.
        """
        if not self._state.can_execute():
            logger.warning(
                f"Cannot execute experiment {self.experiment.id} "
                f"in state {self._state.__class__.__name__}"
            )
            return False
        
        self._transition_to_state(RunningState())
        return True
    
    def transition_to_completed(self) -> bool:
        """
        Transition to completed state.
        Returns True if transition was successful, False otherwise.
        """
        if not self._state.can_complete():
            logger.warning(
                f"Cannot complete experiment {self.experiment.id} "
                f"in state {self._state.__class__.__name__}"
            )
            return False
        
        self._transition_to_state(CompletedState())
        return True
    
    def transition_to_failed(self) -> bool:
        """
        Transition to failed state.
        Returns True if transition was successful, False otherwise.
        """
        if not self._state.can_fail():
            logger.warning(
                f"Cannot mark experiment {self.experiment.id} as failed "
                f"in state {self._state.__class__.__name__}"
            )
            return False
        
        self._transition_to_state(FailedState())
        return True
    
    def _transition_to_state(self, new_state: ExperimentState) -> None:
        """Internal method to perform state transition."""
        old_state = self._state
        old_state.on_exit(self.experiment)
        self._state = new_state
        new_state.on_enter(self.experiment)
        
        # Update the model's status field
        self.experiment.status = new_state.get_status_value()
