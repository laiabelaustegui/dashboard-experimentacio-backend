"""
Business logic for experiments.
Handles experiment execution, LLM interactions, and result processing.
"""
import json
import time
import logging
from typing import List, Dict, Any, Optional
from django.db import transaction

from .models import Experiment, Run, MobileApp, MobileAppRanked, RankingCriteria
from .llm_providers import LLMProviderFactory
from .utils import render_user_prompt_for_feature
from .constants import (
    RESPONSE_FIELD_APPS,
    RESPONSE_FIELD_CRITERIA,
    RESPONSE_FIELD_CRITERIA_NAME,
    RESPONSE_FIELD_CRITERIA_DESCRIPTION,
)

logger = logging.getLogger(__name__)


class ExperimentExecutionService:
    """Service for executing experiments with LLM models."""
    
    def __init__(self, experiment: Experiment):
        self.experiment = experiment
    
    def execute(self) -> List[Dict[str, Any]]:
        """
        Execute the experiment across all configured models.
        
        Returns:
            List of results for each configured model
            
        Raises:
            ValueError: If no configured models or features are found
            RuntimeError: If LLM API calls fail
        """
        configured_models = self.experiment.configured_models.all()
        
        if not configured_models.exists():
            raise ValueError("No configured models found for this experiment.")
        
        all_results = []
        
        try:
            with transaction.atomic():
                for configured_model in configured_models:
                    results = self._execute_configured_model(configured_model)
                    all_results.extend(results)
                
                # Use state pattern to transition to completed
                if not self.experiment.mark_as_completed(save=True):
                    raise RuntimeError("Cannot mark experiment as completed in current state")
                
        except Exception as e:
            logger.error(f"Experiment {self.experiment.id} failed: {str(e)}")
            # Save FAILED status outside transaction to persist even on rollback
            self.experiment.mark_as_failed(save=True)
            raise
        
        return all_results
    
    def _execute_configured_model(self, configured_model) -> List[Dict[str, Any]]:
        """Execute a single configured model across all features."""
        llm_model = configured_model.llm
        configuration = configured_model.configuration
        prompt_template = self.experiment.prompt_template
        
        # Create LLM provider
        provider = LLMProviderFactory.create_provider(
            provider_name=llm_model.provider,
            api_key=llm_model.get_api_key()
        )
        
        # Get prompts and features
        system_prompt = prompt_template.system_prompt.text
        schema = prompt_template.system_prompt.schema
        user_prompt_obj = prompt_template.user_prompt
        features = user_prompt_obj.features.all()
        
        if not features.exists():
            raise ValueError("No features defined for this prompt template.")
        
        results = []
        
        for feature in features:
            feature_results = self._execute_feature(
                provider=provider,
                llm_model=llm_model,
                configuration=configuration,
                system_prompt=system_prompt,
                schema=schema,
                user_prompt_obj=user_prompt_obj,
                feature=feature,
                configured_model=configured_model
            )
            results.extend(feature_results)
        
        return results
    
    def _execute_feature(
        self,
        provider,
        llm_model,
        configuration,
        system_prompt: str,
        schema: Dict[str, Any],
        user_prompt_obj,
        feature,
        configured_model
    ) -> List[Dict[str, Any]]:
        """Execute multiple runs for a single feature."""
        user_prompt = render_user_prompt_for_feature(
            user_prompt=user_prompt_obj,
            feature=feature,
            k=user_prompt_obj.k
        )
        print(user_prompt)
        results = []
        
        for i in range(self.experiment.num_runs):
            logger.info(
                f"Run {i+1}/{self.experiment.num_runs} for model {llm_model.name}, "
                f"feature {feature.id}"
            )
            
            start_time = time.time()
            
            # Prepare top_p parameter (only include if different from default value of 1)
            top_p = None
            if configuration and configuration.topP != 1:
                top_p = configuration.topP
            
            # Execute LLM completion
            content = provider.create_completion(
                model_name=llm_model.name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=schema,
                temperature=configuration.temperature,
                top_p=top_p
            )
            
            elapsed_time = time.time() - start_time
            
            # Create run with results
            run = self._create_run_with_results(
                configured_model=configured_model,
                elapsed_time=elapsed_time,
                output_data=content,
                feature=feature
            )
            
            results.append({
                "run_id": run.id,
                "elapsed_time": elapsed_time,
                "feature_id": feature.id,
            })
        
        return results
    
    def _create_run_with_results(
        self,
        configured_model,
        elapsed_time: float,
        output_data: str,
        feature
    ) -> Run:
        """
        Create a Run instance with associated results.
        
        Args:
            configured_model: The configured model used
            elapsed_time: Time taken to complete the run
            output_data: JSON string containing the LLM response
            feature: The feature being tested
            
        Returns:
            Run: The created Run instance
        """
        try:
            data = json.loads(output_data)
            # Handle double-encoded JSON if LLM returns a JSON string
            if isinstance(data, str):
                data = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
        
        # Create Run instance
        run = Run.objects.create(
            experiment=self.experiment,
            configured_model=configured_model,
            elapsed_time=elapsed_time,
            feature=feature
        )
        
        # Process mobile apps
        self._create_ranked_apps(run, data)
        
        # Process ranking criteria
        self._create_ranking_criteria(run, data)
        
        return run
    
    def _create_ranked_apps(self, run: Run, data: Dict[str, Any]) -> None:
        """Create MobileApp and MobileAppRanked entries."""
        apps_names = data.get(RESPONSE_FIELD_APPS, [])
        
        if not apps_names:
            logger.warning(f"No apps found in response for run {run.id}")
            return
        
        ranked_apps = []
        for idx, app_name in enumerate(apps_names, start=1):
            mobile_app, _ = MobileApp.objects.get_or_create(name=app_name)
            ranked_apps.append(
                MobileAppRanked(
                    mobile_app=mobile_app,
                    run=run,
                    rank=idx
                )
            )
        
        # Bulk create for better performance
        MobileAppRanked.objects.bulk_create(ranked_apps)
    
    def _create_ranking_criteria(self, run: Run, data: Dict[str, Any]) -> None:
        """Create RankingCriteria entries."""
        criteria_list = data.get(RESPONSE_FIELD_CRITERIA, [])
        
        if not criteria_list:
            logger.info(f"No ranking criteria found for run {run.id}")
            return
        
        criteria_objects = []
        for criterion in criteria_list:
            criteria_objects.append(
                RankingCriteria(
                    name=criterion.get(RESPONSE_FIELD_CRITERIA_NAME, 'Unnamed Criterion'),
                    description=criterion.get(RESPONSE_FIELD_CRITERIA_DESCRIPTION, ''),
                    run=run
                )
            )
        
        # Bulk create for better performance
        RankingCriteria.objects.bulk_create(criteria_objects)
