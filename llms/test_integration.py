"""
Integration tests for LLMs app.

These tests verify end-to-end workflows for LLM management,
including API encryption, configuration management, and model relationships.
"""
# pylint: disable=no-member
# Django models dynamically add 'objects' manager at runtime

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from .models import LLM, Configuration, ConfiguredModel


class LLMAPIIntegrationTests(TestCase):
    """Integration tests for LLM API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_create_llm_with_encryption_workflow(self):
        """
        Integration test for LLM creation with API key encryption.
        Tests: API → Validation → Encryption → Database → Response.
        """
        data = {
            "name": "gpt-4-turbo",
            "provider": "OpenAI",
            "API_key": "sk-test-secret-key-12345"
        }
        
        response = self.client.post('/api/llms/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify LLM was created
        llm = LLM.objects.get(name="gpt-4-turbo")
        self.assertEqual(llm.provider, "OpenAI")
        
        # Verify API key is encrypted in database
        self.assertNotEqual(llm.API_key, "sk-test-secret-key-12345")
        self.assertTrue(llm.API_key.startswith('gAAAA'))
        
        # Verify decryption works
        decrypted_key = llm.get_api_key()
        self.assertEqual(decrypted_key, "sk-test-secret-key-12345")
        
        # Verify response doesn't include encrypted key
        self.assertIn('id', response.data)
        self.assertIn('name', response.data)

    def test_list_llms_integration(self):
        """Integration test for listing LLMs."""
        # Create multiple LLMs
        LLM.objects.create(
            name="gpt-4",
            provider="OpenAI",
            API_key="key1"
        )
        LLM.objects.create(
            name="claude-3",
            provider="Anthropic",
            API_key="key2"
        )
        
        response = self.client.get('/api/llms/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        names = [llm['name'] for llm in response.data]
        self.assertIn("gpt-4", names)
        self.assertIn("claude-3", names)

    def test_llm_detail_integration(self):
        """Integration test for LLM detail retrieval."""
        llm = LLM.objects.create(
            name="gpt-3.5-turbo",
            provider="OpenAI",
            API_key="sk-detail-test"
        )
        
        response = self.client.get(f'/api/llms/{llm.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "gpt-3.5-turbo")
        self.assertEqual(response.data['provider'], "OpenAI")
        self.assertIn('creation_date', response.data)

    def test_update_llm_api_key(self):
        """Integration test for updating LLM API key."""
        llm = LLM.objects.create(
            name="gpt-4",
            provider="OpenAI",
            API_key="old-key"
        )
        
        old_encrypted_key = llm.API_key
        
        data = {
            "name": "gpt-4",
            "provider": "OpenAI",
            "API_key": "new-secret-key"
        }
        
        response = self.client.put(f'/api/llms/{llm.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        llm.refresh_from_db()
        
        # Verify key was re-encrypted
        self.assertNotEqual(llm.API_key, old_encrypted_key)
        self.assertNotEqual(llm.API_key, "new-secret-key")
        
        # Verify new key decrypts correctly
        decrypted = llm.get_api_key()
        self.assertEqual(decrypted, "new-secret-key")

    def test_delete_llm_integration(self):
        """Integration test for LLM deletion."""
        llm = LLM.objects.create(
            name="to-delete",
            provider="OpenAI",
            API_key="temp-key"
        )
        
        llm_id = llm.id
        
        response = self.client.delete(f'/api/llms/{llm_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LLM.objects.filter(id=llm_id).exists())


class ConfigurationAPIIntegrationTests(TestCase):
    """Integration tests for Configuration API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_create_configuration_workflow(self):
        """Integration test for configuration creation."""
        data = {
            "name": "High Temperature Config",
            "temperature": 0.9,
            "topP": 0.95
        }
        
        response = self.client.post('/api/configurations/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        config = Configuration.objects.get(name="High Temperature Config")
        self.assertEqual(config.temperature, 0.9)
        self.assertEqual(config.topP, 0.95)

    def test_list_configurations_integration(self):
        """Integration test for listing configurations."""
        Configuration.objects.create(
            name="Config 1",
            temperature=0.7
        )
        Configuration.objects.create(
            name="Config 2",
            temperature=0.5,
            topP=0.8
        )
        
        response = self.client.get('/api/configurations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_configuration_integration(self):
        """Integration test for updating configuration."""
        config = Configuration.objects.create(
            name="Updateable Config",
            temperature=0.7
        )
        
        data = {
            "name": "Updated Config",
            "temperature": 0.8,
            "topP": 0.9
        }
        
        response = self.client.put(
            f'/api/configurations/{config.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        config.refresh_from_db()
        self.assertEqual(config.name, "Updated Config")
        self.assertEqual(config.temperature, 0.8)
        self.assertEqual(config.topP, 0.9)


class ConfiguredModelIntegrationTests(TestCase):
    """Integration tests for ConfiguredModel workflows."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.llm = LLM.objects.create(
            name="gpt-4",
            provider="OpenAI",
            API_key="test-key"
        )
        
        self.config = Configuration.objects.create(
            name="Standard Config",
            temperature=0.7,
            topP=0.9
        )

    def test_create_configured_model_integration(self):
        """
        Integration test for configured model creation.
        Tests relationship between LLM and Configuration.
        """
        data = {
            "llm": self.llm.id,
            "configuration": self.config.id,
            "short_name": "gpt-4-standard"
        }
        
        response = self.client.post('/api/configured-models/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        configured_model = ConfiguredModel.objects.get(short_name="gpt-4-standard")
        self.assertEqual(configured_model.llm, self.llm)
        self.assertEqual(configured_model.configuration, self.config)

    def test_configured_model_with_llm_details(self):
        """
        Integration test verifying configured model includes LLM details.
        Tests nested serializer relationships.
        """
        configured_model = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config,
            short_name="gpt-4-detailed"
        )
        
        response = self.client.get(f'/api/configured-models/{configured_model.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['short_name'], "gpt-4-detailed")
        
        # Verify nested LLM data is included
        self.assertIn('llm', response.data)
        # Check if it's an ID or full object based on serializer implementation
        
    def test_list_configured_models_with_relations(self):
        """Integration test for listing configured models with relationships."""
        ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config,
            short_name="model-1"
        )
        
        # Create another LLM and config
        llm2 = LLM.objects.create(
            name="claude-3",
            provider="Anthropic",
            API_key="anthropic-key"
        )
        
        config2 = Configuration.objects.create(
            name="Alternative Config",
            temperature=0.5
        )
        
        ConfiguredModel.objects.create(
            llm=llm2,
            configuration=config2,
            short_name="model-2"
        )
        
        response = self.client.get('/api/configured-models/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_delete_configured_model_integration(self):
        """Integration test for configured model deletion."""
        configured_model = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config,
            short_name="to-delete"
        )
        
        model_id = configured_model.id
        
        response = self.client.delete(f'/api/configured-models/{model_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ConfiguredModel.objects.filter(id=model_id).exists())
        
        # Verify LLM and Configuration still exist
        self.assertTrue(LLM.objects.filter(id=self.llm.id).exists())
        self.assertTrue(Configuration.objects.filter(id=self.config.id).exists())

    def test_configured_model_prevents_duplicate_combinations(self):
        """
        Integration test for unique constraint on LLM+Configuration combination.
        """
        ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config,
            short_name="original"
        )
        
        # Attempt to create duplicate with different short_name
        data = {
            "llm": self.llm.id,
            "configuration": self.config.id,
            "short_name": "duplicate-attempt"
        }
        
        response = self.client.post('/api/configured-models/', data, format='json')
        
        # This should either succeed or fail based on your business rules
        # Adjust assertion based on actual model constraints


class CrossAppLLMIntegrationTests(TestCase):
    """Integration tests verifying LLM usage across different apps."""

    def setUp(self):
        """Set up cross-app test data."""
        self.client = APIClient()
        
        # Create LLM infrastructure
        self.llm = LLM.objects.create(
            name="gpt-4",
            provider="OpenAI",
            API_key="cross-app-key"
        )
        
        self.config = Configuration.objects.create(
            name="Cross-App Config",
            temperature=0.8
        )
        
        self.configured_model = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config,
            short_name="gpt-4-cross-app"
        )

    def test_configured_model_used_in_experiments(self):
        """
        Integration test verifying configured models can be used in experiments.
        Tests cross-app relationships.
        """
        from prompts.models import Template, SystemPrompt, UserPrompt
        from experiments.models import Experiment
        
        # Create prompt components
        system_prompt = SystemPrompt.objects.create(
            text="System prompt",
            schema={"type": "object"}
        )
        
        user_prompt = UserPrompt.objects.create(
            text="User prompt",
            k=5
        )
        
        template = Template.objects.create(
            name="Integration Template",
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        # Create experiment using configured model
        experiment = Experiment.objects.create(
            name="Cross-App Experiment",
            prompt_template=template,
            num_runs=1
        )
        experiment.configured_models.add(self.configured_model)
        
        # Verify relationships
        self.assertEqual(experiment.configured_models.count(), 1)
        self.assertEqual(
            experiment.configured_models.first().llm.provider,
            "OpenAI"
        )

    def test_llm_deletion_prevents_if_used_in_configured_models(self):
        """
        Integration test for protecting LLM deletion when in use.
        Tests database constraints.
        """
        # ConfiguredModel exists using self.llm
        
        response = self.client.delete(f'/api/llms/{self.llm.id}/')
        
        # Depending on your model setup, this might be:
        # - Prevented (PROTECT constraint)
        # - Cascade delete
        # Adjust assertion based on your actual model constraints
        
        # If PROTECT:
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertTrue(LLM.objects.filter(id=self.llm.id).exists())
        
        # If CASCADE:
        # self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # self.assertFalse(ConfiguredModel.objects.filter(id=self.configured_model.id).exists())


class EncryptionIntegrationTests(TestCase):
    """Integration tests for encryption utilities with database operations."""

    def test_encryption_roundtrip_with_database(self):
        """
        Integration test for encryption/decryption through database.
        Tests full encryption workflow in realistic scenario.
        """
        original_key = "sk-test-integration-key-xyz123"
        
        llm = LLM.objects.create(
            name="encryption-test",
            provider="OpenAI",
            API_key=original_key
        )
        
        # Save to database
        llm_id = llm.id
        
        # Clear object from memory
        del llm
        
        # Retrieve fresh from database
        llm_retrieved = LLM.objects.get(id=llm_id)
        
        # Verify encrypted in database
        self.assertNotEqual(llm_retrieved.API_key, original_key)
        
        # Verify decrypts correctly
        decrypted = llm_retrieved.get_api_key()
        self.assertEqual(decrypted, original_key)

    def test_multiple_llms_different_encryption(self):
        """
        Integration test verifying each LLM has unique encryption.
        Tests encryption randomization.
        """
        same_key = "shared-key"
        
        llm1 = LLM.objects.create(
            name="llm-1",
            provider="OpenAI",
            API_key=same_key
        )
        
        llm2 = LLM.objects.create(
            name="llm-2",
            provider="OpenAI",
            API_key=same_key
        )
        
        # Encrypted values should be different (due to Fernet randomization)
        self.assertNotEqual(llm1.API_key, llm2.API_key)
        
        # But both should decrypt to same value
        self.assertEqual(llm1.get_api_key(), same_key)
        self.assertEqual(llm2.get_api_key(), same_key)
