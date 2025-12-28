from rest_framework import serializers
from .models import Feature, Template, SystemPrompt, UserPrompt

class SystemPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemPrompt
        fields = ['text', 'schema']

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['name', 'description']

class UserPromptSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, required=False)
    class Meta:
        model = UserPrompt
        fields = ['text', 'k', 'features']

class TemplateSerializer(serializers.ModelSerializer):
    system_prompt = SystemPromptSerializer()
    user_prompt = UserPromptSerializer()

    class Meta:
        model = Template
        fields = ['id', 'name', 'creation_date', 'system_prompt', 'user_prompt']

    def create(self, validated_data):
        system_prompt_data = validated_data.pop('system_prompt')
        user_prompt_data = validated_data.pop('user_prompt')
        features_data = user_prompt_data.pop('features', [])

        system_prompt = SystemPrompt.objects.create(**system_prompt_data)
        user_prompt = UserPrompt.objects.create(**user_prompt_data)

        for feature_data in features_data:
            Feature.objects.create(user_prompt=user_prompt, **feature_data)
        
        template = Template.objects.create(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            **validated_data
        )
        return template
