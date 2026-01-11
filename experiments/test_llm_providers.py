"""
Test cases for LLM providers.
"""
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
import json

from .llm_providers import LLMProvider, OpenAIProvider, LLMProviderFactory


class OpenAIProviderTests(TestCase):
    """Test cases for OpenAIProvider."""

    def setUp(self):
        """Set up test data."""
        self.api_key = "test-api-key-123"
        self.provider = OpenAIProvider(api_key=self.api_key)

    @patch('experiments.llm_providers.OpenAI')
    def test_create_completion_success(self, mock_openai_class):
        """Test successful completion creation."""
        # Mock the OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({"result": "success"})
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Create provider (will use mocked OpenAI)
        provider = OpenAIProvider(api_key=self.api_key)
        
        # Execute
        result = provider.create_completion(
            model_name="gpt-4",
            system_prompt="You are helpful",
            user_prompt="Test prompt",
            schema={"type": "json_object"},
            temperature=0.7
        )
        
        self.assertEqual(result, json.dumps({"result": "success"}))
        
        # Verify OpenAI client was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['model'], "gpt-4")
        self.assertEqual(call_kwargs['temperature'], 0.7)
        self.assertNotIn('top_p', call_kwargs)  # Should not be present when None

    @patch('experiments.llm_providers.OpenAI')
    def test_create_completion_with_top_p(self, mock_openai_class):
        """Test completion creation with top_p parameter."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "test content"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(api_key=self.api_key)
        
        result = provider.create_completion(
            model_name="gpt-4",
            system_prompt="System",
            user_prompt="User",
            schema={"type": "json_object"},
            temperature=0.7,
            top_p=0.9
        )
        
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['top_p'], 0.9)

    @patch('experiments.llm_providers.OpenAI')
    def test_create_completion_with_messages(self, mock_openai_class):
        """Test that messages are correctly formatted."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(api_key=self.api_key)
        
        system_prompt = "You are a helpful assistant"
        user_prompt = "What is AI?"
        
        provider.create_completion(
            model_name="gpt-4",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema={"type": "json_object"},
            temperature=0.5
        )
        
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        messages = call_kwargs['messages']
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['role'], 'system')
        self.assertEqual(messages[0]['content'], system_prompt)
        self.assertEqual(messages[1]['role'], 'user')
        self.assertEqual(messages[1]['content'], user_prompt)

    @patch('experiments.llm_providers.OpenAI')
    def test_create_completion_empty_response(self, mock_openai_class):
        """Test handling of empty response from OpenAI."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = None  # Empty response
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(api_key=self.api_key)
        
        with self.assertRaises(RuntimeError) as context:
            provider.create_completion(
                model_name="gpt-4",
                system_prompt="System",
                user_prompt="User",
                schema={"type": "json_object"},
                temperature=0.7
            )
        
        self.assertIn("Empty response", str(context.exception))

    @patch('experiments.llm_providers.OpenAI')
    def test_create_completion_api_error(self, mock_openai_class):
        """Test handling of OpenAI API errors."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(api_key=self.api_key)
        
        with self.assertRaises(RuntimeError) as context:
            provider.create_completion(
                model_name="gpt-4",
                system_prompt="System",
                user_prompt="User",
                schema={"type": "json_object"},
                temperature=0.7
            )
        
        self.assertIn("OpenAI API request failed", str(context.exception))

    @patch('experiments.llm_providers.OpenAI')
    def test_create_completion_with_schema(self, mock_openai_class):
        """Test that schema is correctly passed to API."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "{}"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(api_key=self.api_key)
        
        schema = {"type": "json_object"}
        provider.create_completion(
            model_name="gpt-4",
            system_prompt="System",
            user_prompt="User",
            schema=schema,
            temperature=0.7
        )
        
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['response_format'], schema)


class LLMProviderFactoryTests(TestCase):
    """Test cases for LLMProviderFactory."""

    def test_create_openai_provider(self):
        """Test creating an OpenAI provider."""
        provider = LLMProviderFactory.create_provider(
            provider_name="OpenAI",
            api_key="test-key"
        )
        
        self.assertIsInstance(provider, OpenAIProvider)

    def test_create_unsupported_provider(self):
        """Test creating an unsupported provider raises error."""
        with self.assertRaises(NotImplementedError) as context:
            LLMProviderFactory.create_provider(
                provider_name="UnsupportedProvider",
                api_key="test-key"
            )
        
        self.assertIn("not supported", str(context.exception))
        self.assertIn("Available providers", str(context.exception))

    def test_register_new_provider(self):
        """Test registering a new provider."""
        # Create a mock provider class
        class MockProvider(LLMProvider):
            def __init__(self, api_key):
                self.api_key = api_key
            
            def create_completion(self, model_name, system_prompt, user_prompt, 
                                schema, temperature, top_p=None, timeout=30):
                return "mock response"
        
        # Register it
        LLMProviderFactory.register_provider("MockProvider", MockProvider)
        
        # Create an instance
        provider = LLMProviderFactory.create_provider(
            provider_name="MockProvider",
            api_key="test-key"
        )
        
        self.assertIsInstance(provider, MockProvider)
        self.assertEqual(provider.api_key, "test-key")

    def test_factory_provider_list(self):
        """Test that factory maintains list of available providers."""
        # OpenAI should be in the list by default
        self.assertIn("OpenAI", LLMProviderFactory._providers)

    def test_create_provider_passes_api_key(self):
        """Test that API key is correctly passed to provider."""
        with patch('experiments.llm_providers.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            api_key = "my-secret-key"
            provider = LLMProviderFactory.create_provider(
                provider_name="OpenAI",
                api_key=api_key
            )
            
            # Verify OpenAI was initialized with correct API key
            mock_openai_class.assert_called_once()
            call_kwargs = mock_openai_class.call_args[1]
            self.assertEqual(call_kwargs['api_key'], api_key)


class AbstractLLMProviderTests(TestCase):
    """Test cases for the abstract LLMProvider base class."""

    def test_abstract_provider_cannot_be_instantiated(self):
        """Test that LLMProvider is abstract and cannot be instantiated."""
        with self.assertRaises(TypeError):
            LLMProvider()

    def test_subclass_must_implement_create_completion(self):
        """Test that subclasses must implement create_completion."""
        class IncompleteProvider(LLMProvider):
            pass
        
        with self.assertRaises(TypeError):
            IncompleteProvider()
