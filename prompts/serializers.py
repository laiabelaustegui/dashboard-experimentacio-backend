from rest_framework import serializers
from .models import Template, SystemPrompt, UserPrompt

class SystemPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemPrompt
        fields = ['text', 'schema']

class UserPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPrompt
        fields = ['text']

class TemplateSerializer(serializers.ModelSerializer):
    system_prompt = SystemPromptSerializer()
    user_prompt = UserPromptSerializer()

    class Meta:
        model = Template
        fields = ['id', 'name', 'creation_date', 'system_prompt', 'user_prompt']

    def create(self, validated_data):
        system_prompt_data = validated_data.pop('system_prompt')
        user_prompt_data = validated_data.pop('user_prompt')
        system_prompt = SystemPrompt.objects.create(**system_prompt_data)
        user_prompt = UserPrompt.objects.create(**user_prompt_data)
        template = Template.objects.create(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            **validated_data
        )
        return template
