from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Experiment
from .serializers import ExperimentSerializer
from openai import OpenAI

class CustomExperimentCreate(APIView):
    def post(self, request):
        serializer = ExperimentSerializer(data=request.data)
        if serializer.is_valid():
            experiment = serializer.save()
            prompt_template = experiment.prompt_template
            llm_model = experiment.model
            config = experiment.configuration

            try:
                result = self.execute_model(llm_model, prompt_template, config)
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


    def execute_model(self, llm_model, prompt_template, config):
        #Todo: Improve this to support multiple providers and configurations
        if (llm_model.provider == "OpenAI"):
            api_key = llm_model.get_api_key()
            client = OpenAI(api_key=api_key)
            print("Sending request to OpenAI...")
            print(f"Model: {llm_model.name}")
            response = client.responses.create(
                model=llm_model.name,
                input=prompt_template.user_prompt.text,
                #instructions=prompt_template.system_prompt.text,
            )
            return response.output_text
        else:
            raise NotImplementedError(f"Provider {llm_model.provider} not supported yet.")
