from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Experiment
from .serializers import ExperimentSerializer

class CustomExperimentCreate(APIView):
    def post(self, request):
        serializer = ExperimentSerializer(data=request.data)
        if serializer.is_valid():
            experiment = serializer.save()
            
            # Aquí va tu lógica de ejecución automática
            prompt_template = experiment.prompt_template
            llm_model = experiment.model
            config = experiment.configuration
            
            # Ejemplo pseudocódigo: llamada al modelo
            result = self.execute_model(llm_model, prompt_template, config)
            
            if not result:
                experiment.status = Experiment.Status.FAILED
                experiment.save()
                return Response({"error": "Model execution failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Aquí puedes actualizar el experimento, crear una Run, capturar logs, etc.
            experiment.status = Experiment.Status.COMPLETED  # Si terminó correctamente
            experiment.save()
            
            return Response(ExperimentSerializer(experiment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def execute_model(self, llm_model, prompt_template, config):
        # Aquí llamas a tu modelo LLM con los datos necesarios y obtienes el resultado
        # Por ejemplo, podrías integrar una librería externa, API, etc.
        if (llm_model.provider == "OpenAI"):
            from openai import OpenAI
            api_key = llm_model.get_api_key()
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=llm_model.name,
                input=prompt_template.user_prompt.text,
                #instructions=prompt_template.system_prompt.text,
            )
            return response.output_text
    


