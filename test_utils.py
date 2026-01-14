"""
Test cases for utility functions.
"""
from django.test import TestCase
from cryptography.fernet import Fernet
from django.conf import settings

from llms.utils import encrypt, decrypt
from experiments.utils import render_user_prompt_for_feature
from prompts.models import UserPrompt, Feature


class EncryptionUtilsTests(TestCase):
    """Test cases for encryption/decryption utilities."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        original_text = "my-secret-api-key"
        
        encrypted = encrypt(original_text)
        decrypted = decrypt(encrypted)
        
        self.assertEqual(decrypted, original_text)
        self.assertNotEqual(encrypted, original_text)

    def test_encrypt_produces_fernet_format(self):
        """Test that encrypted text is in Fernet format."""
        text = "test-key"
        encrypted = encrypt(text)
        
        # Fernet tokens start with 'gAAAA'
        self.assertTrue(encrypted.startswith('gAAAA'))

    def test_encrypt_different_inputs_produce_different_outputs(self):
        """Test that different inputs produce different encrypted outputs."""
        text1 = "key1"
        text2 = "key2"
        
        encrypted1 = encrypt(text1)
        encrypted2 = encrypt(text2)
        
        self.assertNotEqual(encrypted1, encrypted2)

    def test_encrypt_same_input_produces_different_outputs(self):
        """Test that encrypting the same input twice produces different ciphertexts."""
        text = "same-key"
        
        encrypted1 = encrypt(text)
        encrypted2 = encrypt(text)
        
        # Fernet includes a timestamp, so same plaintext can produce different ciphertexts
        # But both should decrypt to the same value
        self.assertEqual(decrypt(encrypted1), text)
        self.assertEqual(decrypt(encrypted2), text)

    def test_decrypt_invalid_token_raises_error(self):
        """Test that decrypting invalid token raises an error."""
        invalid_token = "not-a-valid-fernet-token"
        
        with self.assertRaises(Exception):
            decrypt(invalid_token)

    def test_encrypt_empty_string(self):
        """Test encrypting an empty string."""
        encrypted = encrypt("")
        decrypted = decrypt(encrypted)
        
        self.assertEqual(decrypted, "")

    def test_encrypt_long_string(self):
        """Test encrypting a long string."""
        long_text = "a" * 1000
        
        encrypted = encrypt(long_text)
        decrypted = decrypt(encrypted)
        
        self.assertEqual(decrypted, long_text)

    def test_encrypt_special_characters(self):
        """Test encrypting strings with special characters."""
        special_text = "key!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        
        encrypted = encrypt(special_text)
        decrypted = decrypt(encrypted)
        
        self.assertEqual(decrypted, special_text)

    def test_encrypt_unicode_characters(self):
        """Test encrypting strings with unicode characters."""
        unicode_text = "key-with-emoji-🔐-and-中文"
        
        encrypted = encrypt(unicode_text)
        decrypted = decrypt(encrypted)
        
        self.assertEqual(decrypted, unicode_text)


class RenderUserPromptTests(TestCase):
    """Test cases for render_user_prompt_for_feature utility."""

    def setUp(self):
        """Set up test data."""
        self.user_prompt = UserPrompt.objects.create(
            text="Analyze the feature: {{ feature }}",
            k=5
        )
        self.feature = Feature.objects.create(
            name="Search",
            description="Search functionality",
            user_prompt=self.user_prompt
        )

    def test_render_with_feature_only(self):
        """Test rendering with feature variable only."""
        user_prompt = UserPrompt.objects.create(
            text="Feature name is {{ feature }}",
            k=None
        )
        feature = Feature.objects.create(
            name="Login",
            user_prompt=user_prompt
        )
        
        result = render_user_prompt_for_feature(user_prompt, feature)
        
        self.assertEqual(result, "Feature name is login")

    def test_render_with_feature_and_k(self):
        """Test rendering with both feature and k variables."""
        user_prompt = UserPrompt.objects.create(
            text="Feature: {{ feature }}, K: {{ k }}",
            k=10
        )
        feature = Feature.objects.create(
            name="Navigation",
            user_prompt=user_prompt
        )
        
        result = render_user_prompt_for_feature(user_prompt, feature, k=10)
        
        self.assertEqual(result, "Feature: navigation, K: 10")

    def test_render_complex_template(self):
        """Test rendering a more complex Jinja2 template."""
        user_prompt = UserPrompt.objects.create(
            text="Please recommend {{ k }} apps for {{ feature }} feature.",
            k=5
        )
        feature = Feature.objects.create(
            name="photo editing",
            user_prompt=user_prompt
        )
        
        result = render_user_prompt_for_feature(user_prompt, feature, k=5)
        
        self.assertEqual(result, "Please recommend 5 apps for photo editing feature.")

    def test_render_without_k_parameter(self):
        """Test rendering when k is None."""
        user_prompt = UserPrompt.objects.create(
            text="Analyze {{ feature }}",
            k=None
        )
        feature = Feature.objects.create(
            name="Settings",
            user_prompt=user_prompt
        )
        
        result = render_user_prompt_for_feature(user_prompt, feature, k=None)
        
        self.assertEqual(result, "Analyze settings")

    def test_render_with_k_in_template_but_no_k_provided(self):
        """Test rendering when template has k but k is not provided."""
        user_prompt = UserPrompt.objects.create(
            text="Recommend apps for {{ feature }}",
            k=None
        )
        feature = Feature.objects.create(
            name="gaming",
            user_prompt=user_prompt
        )
        
        # When k is None, it shouldn't be in the context
        result = render_user_prompt_for_feature(user_prompt, feature, k=None)
        
        self.assertEqual(result, "Recommend apps for gaming")

    def test_render_preserves_formatting(self):
        """Test that rendering preserves text formatting."""
        user_prompt = UserPrompt.objects.create(
            text="""Please analyze the {{ feature }} feature.
            
This is a multi-line template with {{ k }} recommendations.""",
            k=3
        )
        feature = Feature.objects.create(
            name="messaging",
            user_prompt=user_prompt
        )
        
        result = render_user_prompt_for_feature(user_prompt, feature, k=3)
        
        self.assertIn("Please analyze the messaging feature.", result)
        self.assertIn("3 recommendations.", result)

    def test_render_feature_with_special_characters(self):
        """Test rendering feature names with special characters."""
        user_prompt = UserPrompt.objects.create(
            text="Feature: {{ feature }}",
            k=None
        )
        feature = Feature.objects.create(
            name="Photo & Video Editing",
            user_prompt=user_prompt
        )
        
        result = render_user_prompt_for_feature(user_prompt, feature)
        
        self.assertEqual(result, "Feature: photo & Video Editing")

    def test_render_with_jinja2_filters(self):
        """Test using Jinja2 filters in the template."""
        user_prompt = UserPrompt.objects.create(
            text="Feature: {{ feature|upper }}, Count: {{ k }}",
            k=7
        )
        feature = Feature.objects.create(
            name="search",
            user_prompt=user_prompt
        )
        
        result = render_user_prompt_for_feature(user_prompt, feature, k=7)
        
        self.assertEqual(result, "Feature: SEARCH, Count: 7")

    def test_render_with_conditional_logic(self):
        """Test using conditional logic in Jinja2 template."""
        user_prompt = UserPrompt.objects.create(
            text="Recommend {% if k %}{{ k }}{% else %}some{% endif %} {{ feature }} apps",
            k=5
        )
        feature = Feature.objects.create(
            name="productivity",
            user_prompt=user_prompt
        )
        
        result = render_user_prompt_for_feature(user_prompt, feature, k=5)
        self.assertEqual(result, "Recommend 5 productivity apps")
        
        # Without k
        result_no_k = render_user_prompt_for_feature(user_prompt, feature, k=None)
        self.assertEqual(result_no_k, "Recommend some productivity apps")
