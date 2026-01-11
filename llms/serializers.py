from rest_framework import serializers
from .models import LLM, Configuration, ConfiguredModel

class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuration
        fields = '__all__'

class LLMSerializer(serializers.ModelSerializer):
    configurations = ConfigurationSerializer(many=True, read_only=True)

    class Meta:
        model = LLM
        fields = ['id', 'name', 'provider', 'API_endpoint', 'API_key', 'creation_date', 'configurations']
        extra_kwargs = {
            'API_key': {'write_only': True},
        }
        
class ConfiguredModelSerializer(serializers.ModelSerializer):
    llm_name = serializers.SerializerMethodField()
    configuration_name = serializers.SerializerMethodField()
    temperature = serializers.SerializerMethodField()
    topP = serializers.SerializerMethodField()
    
    class Meta:
        model = ConfiguredModel
        fields = ['id', 'llm', 'configuration', 'short_name', 'llm_name', 'configuration_name', 'temperature', 'topP']
    
    def get_llm_name(self, obj):
        return obj.llm.name
    
    def get_configuration_name(self, obj):
        return obj.configuration.name
    
    def get_temperature(self, obj):
        return obj.configuration.temperature
    
    def get_topP(self, obj):
        return obj.configuration.topP
    
    def validate(self, attrs):
        """Validate that the combination of llm and configuration is unique"""
        llm = attrs.get('llm')
        configuration = attrs.get('configuration')
        
        # Check if this is an update (instance exists)
        if self.instance:
            # Exclude current instance from the check
            existing = ConfiguredModel.objects.filter(
                llm=llm, 
                configuration=configuration
            ).exclude(id=self.instance.id)
        else:
            # For creation, just check if combination exists
            existing = ConfiguredModel.objects.filter(
                llm=llm, 
                configuration=configuration
            )
        
        if existing.exists():
            existing_model = existing.first()
            raise serializers.ValidationError({
                'non_field_errors': [
                    f'A configured model already exists with this LLM and Configuration combination: "{existing_model.short_name}". '
                    f'Please choose a different LLM or Configuration.'
                ]
            })
        
        return attrs
