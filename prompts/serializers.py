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

    def update(self, instance, validated_data):
        # Update template name
        instance.name = validated_data.get('name', instance.name)
        
        # Update system prompt
        system_prompt_data = validated_data.get('system_prompt')
        if system_prompt_data:
            for attr, value in system_prompt_data.items():
                setattr(instance.system_prompt, attr, value)
            instance.system_prompt.save()
        
        # Update user prompt
        user_prompt_data = validated_data.get('user_prompt')
        if user_prompt_data:
            # Extract features before updating user prompt
            features_data = user_prompt_data.pop('features', None)
            
            # Update user prompt fields
            for attr, value in user_prompt_data.items():
                setattr(instance.user_prompt, attr, value)
            instance.user_prompt.save()
            
            # Update features if provided
            if features_data is not None:
                # Delete existing features
                instance.user_prompt.features.all().delete()
                
                # Create new features
                for feature_data in features_data:
                    Feature.objects.create(user_prompt=instance.user_prompt, **feature_data)
        
        instance.save()
        return instance
