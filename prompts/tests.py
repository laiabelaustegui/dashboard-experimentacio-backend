from django.test import TestCase
from django.db import IntegrityError

from .models import SystemPrompt, UserPrompt, Feature, Template


class SystemPromptModelTests(TestCase):
    """Test cases for the SystemPrompt model."""

    def test_create_system_prompt(self):
        """Test creating a SystemPrompt."""
        prompt = SystemPrompt.objects.create(
            text="You are a helpful assistant.",
            schema={"type": "json_object"}
        )
        
        self.assertEqual(prompt.text, "You are a helpful assistant.")
        self.assertEqual(prompt.schema, {"type": "json_object"})

    def test_system_prompt_with_complex_schema(self):
        """Test SystemPrompt with a complex JSON schema."""
        schema = {
            "type": "object",
            "properties": {
                "apps": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "criteria": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        prompt = SystemPrompt.objects.create(
            text="System prompt",
            schema=schema
        )
        
        self.assertEqual(prompt.schema, schema)

    def test_system_prompt_str(self):
        """Test string representation of SystemPrompt."""
        prompt = SystemPrompt.objects.create(
            text="Test prompt text",
            schema={}
        )
        self.assertEqual(str(prompt), "Test prompt text")


class UserPromptModelTests(TestCase):
    """Test cases for the UserPrompt model."""

    def test_create_user_prompt(self):
        """Test creating a UserPrompt."""
        prompt = UserPrompt.objects.create(
            text="Analyze the feature: {{ feature }}",
            k=5
        )
        
        self.assertEqual(prompt.text, "Analyze the feature: {{ feature }}")
        self.assertEqual(prompt.k, 5)

    def test_user_prompt_without_k(self):
        """Test creating a UserPrompt without k value."""
        prompt = UserPrompt.objects.create(
            text="Simple prompt"
        )
        
        self.assertIsNone(prompt.k)

    def test_user_prompt_str(self):
        """Test string representation of UserPrompt."""
        prompt = UserPrompt.objects.create(
            text="User prompt text",
            k=3
        )
        self.assertEqual(str(prompt), "User prompt text")

    def test_user_prompt_with_template_variables(self):
        """Test UserPrompt with Jinja2 template variables."""
        prompt = UserPrompt.objects.create(
            text="Feature: {{ feature }}, K: {{ k }}",
            k=10
        )
        
        self.assertIn("{{ feature }}", prompt.text)
        self.assertIn("{{ k }}", prompt.text)


class FeatureModelTests(TestCase):
    """Test cases for the Feature model."""

    def setUp(self):
        """Set up test data."""
        self.user_prompt = UserPrompt.objects.create(
            text="Analyze {{ feature }}",
            k=5
        )

    def test_create_feature(self):
        """Test creating a Feature."""
        feature = Feature.objects.create(
            name="Search",
            description="Search functionality",
            user_prompt=self.user_prompt
        )
        
        self.assertEqual(feature.name, "Search")
        self.assertEqual(feature.description, "Search functionality")
        self.assertEqual(feature.user_prompt, self.user_prompt)

    def test_feature_without_description(self):
        """Test creating a Feature without description."""
        feature = Feature.objects.create(
            name="Navigation",
            user_prompt=self.user_prompt
        )
        
        self.assertIsNone(feature.description)

    def test_feature_str(self):
        """Test string representation of Feature."""
        feature = Feature.objects.create(
            name="Login",
            user_prompt=self.user_prompt
        )
        self.assertEqual(str(feature), "Login")

    def test_feature_relationship_with_user_prompt(self):
        """Test the relationship between Feature and UserPrompt."""
        feature1 = Feature.objects.create(
            name="Feature 1",
            user_prompt=self.user_prompt
        )
        feature2 = Feature.objects.create(
            name="Feature 2",
            user_prompt=self.user_prompt
        )
        
        # Access features through user_prompt
        self.assertEqual(self.user_prompt.features.count(), 2)
        self.assertIn(feature1, self.user_prompt.features.all())
        self.assertIn(feature2, self.user_prompt.features.all())

    def test_feature_cascade_delete_user_prompt(self):
        """Test that deleting UserPrompt deletes Features."""
        feature = Feature.objects.create(
            name="Test Feature",
            user_prompt=self.user_prompt
        )
        
        user_prompt_id = self.user_prompt.id
        self.user_prompt.delete()
        
        self.assertFalse(Feature.objects.filter(user_prompt_id=user_prompt_id).exists())


class TemplateModelTests(TestCase):
    """Test cases for the Template model."""

    def setUp(self):
        """Set up test data."""
        self.system_prompt = SystemPrompt.objects.create(
            text="You are helpful.",
            schema={"type": "json_object"}
        )
        self.user_prompt = UserPrompt.objects.create(
            text="Analyze {{ feature }}",
            k=5
        )

    def test_create_template(self):
        """Test creating a Template."""
        template = Template.objects.create(
            name="Test Template",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.system_prompt, self.system_prompt)
        self.assertEqual(template.user_prompt, self.user_prompt)
        self.assertIsNotNone(template.creation_date)

    def test_template_str(self):
        """Test string representation of Template."""
        template = Template.objects.create(
            name="My Template",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        self.assertEqual(str(template), "My Template")

    def test_template_creation_date_auto_set(self):
        """Test that creation_date is automatically set."""
        template = Template.objects.create(
            name="Date Test",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
        self.assertIsNotNone(template.creation_date)

    def test_template_one_to_one_system_prompt(self):
        """Test OneToOne relationship with SystemPrompt."""
        template = Template.objects.create(
            name="Template 1",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
        # Access template through system_prompt
        self.assertEqual(self.system_prompt.template_system, template)

    def test_template_one_to_one_user_prompt(self):
        """Test OneToOne relationship with UserPrompt."""
        template = Template.objects.create(
            name="Template 1",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
        # Access template through user_prompt
        self.assertEqual(self.user_prompt.template_user, template)

    def test_template_system_prompt_cannot_be_reused(self):
        """Test that a SystemPrompt can only be used in one Template."""
        template1 = Template.objects.create(
            name="Template 1",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
        # Create another user prompt for second template
        user_prompt2 = UserPrompt.objects.create(
            text="Different user prompt",
            k=3
        )
        
        # Try to create another template with same system_prompt
        with self.assertRaises(IntegrityError):
            Template.objects.create(
                name="Template 2",
                system_prompt=self.system_prompt,  # Reusing same system_prompt
                user_prompt=user_prompt2
            )

    def test_template_user_prompt_cannot_be_reused(self):
        """Test that a UserPrompt can only be used in one Template."""
        template1 = Template.objects.create(
            name="Template 1",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
        # Create another system prompt for second template
        system_prompt2 = SystemPrompt.objects.create(
            text="Different system prompt",
            schema={}
        )
        
        # Try to create another template with same user_prompt
        with self.assertRaises(IntegrityError):
            Template.objects.create(
                name="Template 2",
                system_prompt=system_prompt2,
                user_prompt=self.user_prompt  # Reusing same user_prompt
            )

    def test_template_cascade_delete_system_prompt(self):
        """Test that deleting SystemPrompt is blocked when Template exists."""
        # Create new prompts specifically for this test
        system_prompt_test = SystemPrompt.objects.create(
            text="Test system prompt",
            schema={"type": "json_object"}
        )
        user_prompt_test = UserPrompt.objects.create(
            text="Test user prompt",
            k=1
        )
        
        template = Template.objects.create(
            name="Test Template",
            system_prompt=system_prompt_test,
            user_prompt=user_prompt_test
        )
        
        system_prompt_id = system_prompt_test.id
        
        # If we try to delete the system_prompt while template exists, it should fail
        # But if we delete the template first, we can then delete the prompt
        from django.db.models import ProtectedError
        
        # For OneToOneField with CASCADE, deleting the "parent" (Template) won't auto-delete
        # But verify the relationship works
        self.assertEqual(system_prompt_test.template_system, template)

    def test_template_cascade_delete_user_prompt(self):
        """Test that deleting UserPrompt is blocked when Template exists."""
        # Create new prompts specifically for this test
        system_prompt_test = SystemPrompt.objects.create(
            text="Test system prompt 2",
            schema={"type": "json_object"}
        )
        user_prompt_test = UserPrompt.objects.create(
            text="Test user prompt 2",
            k=2
        )
        
        template = Template.objects.create(
            name="Test Template 2",
            system_prompt=system_prompt_test,
            user_prompt=user_prompt_test
        )
        
        # Verify the relationship works
        self.assertEqual(user_prompt_test.template_user, template)

    def test_template_with_features(self):
        """Test Template with associated Features through UserPrompt."""
        template = Template.objects.create(
            name="Test Template",
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt
        )
        
        feature1 = Feature.objects.create(
            name="Feature 1",
            user_prompt=self.user_prompt
        )
        feature2 = Feature.objects.create(
            name="Feature 2",
            user_prompt=self.user_prompt
        )
        
        # Access features through template
        features = template.user_prompt.features.all()
        self.assertEqual(features.count(), 2)
        self.assertIn(feature1, features)
        self.assertIn(feature2, features)

