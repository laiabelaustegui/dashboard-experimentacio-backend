from django.test import TestCase
from django.db import IntegrityError
from django.conf import settings

from .models import LLM, Configuration, ConfiguredModel
from .utils import encrypt, decrypt


class ConfigurationModelTests(TestCase):
    """Test cases for the Configuration model."""

    def test_create_configuration_with_defaults(self):
        """Test creating a configuration with default values."""
        config = Configuration.objects.create()
        
        self.assertEqual(config.name, "Default Configuration")
        self.assertEqual(config.temperature, 0.7)
        self.assertIsNone(config.topP)

    def test_create_configuration_with_custom_values(self):
        """Test creating a configuration with custom values."""
        config = Configuration.objects.create(
            name="Custom Config",
            temperature=0.5,
            topP=0.9
        )
        
        self.assertEqual(config.name, "Custom Config")
        self.assertEqual(config.temperature, 0.5)
        self.assertEqual(config.topP, 0.9)

    def test_configuration_str(self):
        """Test string representation of Configuration."""
        config = Configuration.objects.create(name="Test Config")
        self.assertEqual(str(config), "Test Config")

    def test_configuration_temperature_validation(self):
        """Test that temperature accepts valid float values."""
        config = Configuration.objects.create(
            name="Valid Temps",
            temperature=0.0
        )
        self.assertEqual(config.temperature, 0.0)
        
        config.temperature = 2.0
        config.save()
        self.assertEqual(config.temperature, 2.0)


class LLMModelTests(TestCase):
    """Test cases for the LLM model."""

    def test_create_llm(self):
        """Test creating an LLM."""
        llm = LLM.objects.create(
            name="gpt-4",
            provider="OpenAI",
            API_key="test-key-123"
        )
        
        self.assertEqual(llm.name, "gpt-4")
        self.assertEqual(llm.provider, "OpenAI")
        self.assertIsNotNone(llm.creation_date)
        # API key should be encrypted
        self.assertNotEqual(llm.API_key, "test-key-123")

    def test_llm_api_key_encryption(self):
        """Test that API key is encrypted on save."""
        original_key = "my-secret-key"
        llm = LLM.objects.create(
            name="test-model",
            provider="OpenAI",
            API_key=original_key
        )
        
        # Stored key should be encrypted
        self.assertNotEqual(llm.API_key, original_key)
        # Should start with Fernet prefix
        self.assertTrue(llm.API_key.startswith('gAAAA'))

    def test_llm_get_api_key_decryption(self):
        """Test that get_api_key returns decrypted key."""
        original_key = "my-secret-key"
        llm = LLM.objects.create(
            name="test-model",
            provider="OpenAI",
            API_key=original_key
        )
        
        decrypted_key = llm.get_api_key()
        self.assertEqual(decrypted_key, original_key)

    def test_llm_api_key_not_double_encrypted(self):
        """Test that saving an LLM multiple times doesn't double-encrypt."""
        original_key = "test-key"
        llm = LLM.objects.create(
            name="test-model",
            provider="OpenAI",
            API_key=original_key
        )
        
        encrypted_once = llm.API_key
        
        # Save again
        llm.save()
        
        # Should remain the same
        self.assertEqual(llm.API_key, encrypted_once)
        # And still decrypt correctly
        self.assertEqual(llm.get_api_key(), original_key)

    def test_llm_with_api_endpoint(self):
        """Test creating an LLM with custom API endpoint."""
        llm = LLM.objects.create(
            name="custom-model",
            provider="Custom",
            API_key="key",
            API_endpoint="https://custom-api.com/v1"
        )
        
        self.assertEqual(llm.API_endpoint, "https://custom-api.com/v1")

    def test_llm_str(self):
        """Test string representation of LLM."""
        llm = LLM.objects.create(
            name="gpt-3.5-turbo",
            provider="OpenAI",
            API_key="key"
        )
        self.assertEqual(str(llm), "gpt-3.5-turbo")

    def test_llm_creation_date_auto_set(self):
        """Test that creation_date is automatically set."""
        llm = LLM.objects.create(
            name="test",
            provider="OpenAI",
            API_key="key"
        )
        
        self.assertIsNotNone(llm.creation_date)


class ConfiguredModelTests(TestCase):
    """Test cases for the ConfiguredModel model."""

    def setUp(self):
        """Set up test data."""
        self.config1 = Configuration.objects.create(
            name="Config 1",
            temperature=0.7
        )
        self.config2 = Configuration.objects.create(
            name="Config 2",
            temperature=0.3
        )
        self.llm = LLM.objects.create(
            name="gpt-4",
            provider="OpenAI",
            API_key="test-key"
        )

    def test_create_configured_model(self):
        """Test creating a ConfiguredModel."""
        configured = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config1,
            short_name="gpt-4-creative"
        )
        
        self.assertEqual(configured.llm, self.llm)
        self.assertEqual(configured.configuration, self.config1)
        self.assertEqual(configured.short_name, "gpt-4-creative")

    def test_configured_model_unique_together(self):
        """Test that llm+configuration must be unique."""
        ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config1,
            short_name="first"
        )
        
        # Try to create another with same llm+config
        with self.assertRaises(IntegrityError):
            ConfiguredModel.objects.create(
                llm=self.llm,
                configuration=self.config1,
                short_name="second"
            )

    def test_configured_model_different_configs_allowed(self):
        """Test that same LLM with different configs is allowed."""
        cm1 = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config1,
            short_name="gpt-4-config1"
        )
        cm2 = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config2,
            short_name="gpt-4-config2"
        )
        
        self.assertEqual(ConfiguredModel.objects.filter(llm=self.llm).count(), 2)

    def test_configured_model_str(self):
        """Test string representation of ConfiguredModel."""
        configured = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config1,
            short_name="test-model"
        )
        
        expected = f"test-model (gpt-4 - Config 1)"
        self.assertEqual(str(configured), expected)

    def test_configured_model_ordering(self):
        """Test that ConfiguredModels are ordered by llm name."""
        llm1 = LLM.objects.create(name="aaa-model", provider="OpenAI", API_key="key1")
        llm2 = LLM.objects.create(name="zzz-model", provider="OpenAI", API_key="key2")
        
        cm2 = ConfiguredModel.objects.create(
            llm=llm2,
            configuration=self.config1,
            short_name="z-model"
        )
        cm1 = ConfiguredModel.objects.create(
            llm=llm1,
            configuration=self.config1,
            short_name="a-model"
        )
        
        models = list(ConfiguredModel.objects.all())
        # First one should be aaa-model (alphabetically)
        self.assertEqual(models[0].llm.name, "aaa-model")
        # Last one should be zzz-model
        self.assertEqual(models[-1].llm.name, "zzz-model")

    def test_configured_model_cascade_delete_llm(self):
        """Test that deleting LLM deletes ConfiguredModel."""
        configured = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config1,
            short_name="test"
        )
        
        llm_id = self.llm.id
        self.llm.delete()
        
        self.assertFalse(ConfiguredModel.objects.filter(llm_id=llm_id).exists())

    def test_configured_model_cascade_delete_configuration(self):
        """Test that deleting Configuration deletes ConfiguredModel."""
        configured = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config1,
            short_name="test"
        )
        
        config_id = self.config1.id
        self.config1.delete()
        
        self.assertFalse(ConfiguredModel.objects.filter(configuration_id=config_id).exists())

    def test_configured_model_relationship_with_llm(self):
        """Test the relationship between ConfiguredModel and LLM."""
        cm1 = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config1,
            short_name="cm1"
        )
        cm2 = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config2,
            short_name="cm2"
        )
        
        # Access configured models through LLM
        self.assertEqual(self.llm.configuredmodel_set.count(), 2)

    def test_configured_model_relationship_with_configuration(self):
        """Test the relationship between ConfiguredModel and Configuration."""
        llm2 = LLM.objects.create(name="gpt-3.5", provider="OpenAI", API_key="key2")
        
        cm1 = ConfiguredModel.objects.create(
            llm=self.llm,
            configuration=self.config1,
            short_name="cm1"
        )
        cm2 = ConfiguredModel.objects.create(
            llm=llm2,
            configuration=self.config1,
            short_name="cm2"
        )
        
        # Access configured models through Configuration
        self.assertEqual(self.config1.configuredmodel_set.count(), 2)

