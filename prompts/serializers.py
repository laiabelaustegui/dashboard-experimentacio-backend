from rest_framework import serializers
from .models import Feature, Template, SystemPrompt, UserPrompt

class SystemPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemPrompt
        fields = ['text', 'schema']

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'name', 'description', 'user_prompt']
        read_only_fields = ['id', 'user_prompt']  # user_prompt is set automatically when nested

class UserPromptSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, required=False)
    class Meta:
        model = UserPrompt
        fields = ['text', 'k', 'features']

class TemplateSerializer(serializers.ModelSerializer):
    system_prompt = SystemPromptSerializer()
    user_prompt = UserPromptSerializer()
    experiments_count = serializers.SerializerMethodField()

    class Meta:
        model = Template
        fields = ['id', 'name', 'creation_date', 'system_prompt', 'user_prompt', 'experiments_count']
    
    def get_experiments_count(self, obj):
        return obj.experiment_set.count()

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
