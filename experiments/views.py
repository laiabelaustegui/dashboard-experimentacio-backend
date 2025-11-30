from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Experiment
from .serializers import ExperimentSerializer
from openai import OpenAI

class ExperimentViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete']
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer

    def create(self, request, *args, **kwargs):
        serializer = ExperimentSerializer(data=request.data)
        if serializer.is_valid():
            experiment = serializer.save()
            prompt_template = experiment.prompt_template
            # De momento asusmimos un solo modelo configurado por experimento
            configurated_model = experiment.configurated_models.first()

            try:
                result = self.execute_model(configurated_model, prompt_template)
                if not result:
                    raise ValueError("Model response empty or invalid.")
                experiment.status = Experiment.Status.COMPLETED
            except Exception as e:
                experiment.status = Experiment.Status.FAILED
                experiment.save()
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            experiment.save()
            return Response({
                "experiment": ExperimentSerializer(experiment).data,
                "output": result  # aquí ves directamente el output
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Method using chat completions API
    def execute_model(self, configurated_model, prompt_template):
        #Todo: Improve this to support multiple providers and configurations. Also implement runs tracking.
        llm_model = configurated_model.llm
        configuration = configurated_model.configuration
        if (llm_model.provider == "OpenAI"):
            api_key = llm_model.get_api_key()
            client = OpenAI(api_key=api_key)
            system_prompt = prompt_template.system_prompt.text
            user_prompt = prompt_template.user_prompt.text
            schema = prompt_template.system_prompt.schema
            temperature = configuration.temperature

            params = {
                "model": llm_model.name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": schema,
                "temperature": temperature,
            }
            
            if configuration and configuration.topP is not None:
                params["top_p"] = configuration.topP

            try:
                response = client.chat.completions.create(**params)
                return response.choices[0].message.content
            
            except Exception as e:
                raise RuntimeError(f"OpenAI API request failed: {str(e)}")
        else:
            raise NotImplementedError(f"Provider {llm_model.provider} not supported yet.")

     
        #  Method for responses API
        # def execute_model(self, llm_model, prompt_template, config):
        # Todo: Improve this to support multiple providers and configurations. Also implement runs tracking.
        # if (llm_model.provider == "OpenAI"):
        #     api_key = llm_model.get_api_key()
        #     client = OpenAI(api_key=api_key)
        #     print("Sending request to OpenAI...")
        #     print(f"Model: {llm_model.name}")
        #     system_prompt = prompt_template.system_prompt.text
        #     user_prompt = prompt_template.user_prompt.text
        #     schema = prompt_template.system_prompt.schema
        #     try:
        #         response = client.responses.create(
        #             model=llm_model.name,
        #             input=user_prompt,
        #             instructions=system_prompt,
        #             text={"format": schema},
        #         )
        #         return response.output_text
        #     except Exception as e:
        #         raise RuntimeError(f"OpenAI API request failed: {str(e)}")
        # else:
        #     raise NotImplementedError(f"Provider {llm_model.provider} not supported yet.")

