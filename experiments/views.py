from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Experiment, Run, MobileApp, MobileAppRanked, RankingCriteria
from .serializers import ExperimentSerializer, MobileAppSerializer, RankingCriteriaSerializer
from openai import OpenAI
import time
import json

class ExperimentViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete']
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer

    def create(self, request, *args, **kwargs):
        serializer = ExperimentSerializer(data=request.data)
        if serializer.is_valid():
            experiment = serializer.save()
            prompt_template = experiment.prompt_template
            # Get all configured models associated with the experiment
            configured_models = experiment.configured_models.all()
            runs = experiment.num_runs

            if not configured_models.exists():
                return Response({"error": "No configured models found for this experiment."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                for configured_model in configured_models:
                    result = self.execute_model(experiment, configured_model, prompt_template, runs)
                    if not result:
                        raise ValueError("Model response empty or invalid.")
                    print(f"Model response: {result}")
                experiment.status = Experiment.Status.COMPLETED
            except Exception as e:
                experiment.status = Experiment.Status.FAILED
                experiment.save()
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            experiment.save()
            return Response({
                "experiment": ExperimentSerializer(experiment).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Method using chat completions API
    def execute_model(self, experiment, configured_model, prompt_template, runs):
        #Todo: Improve this to support multiple features
        llm_model = configured_model.llm
        configuration = configured_model.configuration
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
            
            results = []

            for i in range(runs):
                print(f"Run {i+1}/{runs} for model {llm_model.name}...")
                start = time.time()

                try:
                    response = client.chat.completions.create(**params)
                    content = response.choices[0].message.content
                except Exception as e:
                    raise RuntimeError(f"OpenAI API request failed: {str(e)}")
                end = time.time()
                elapsed = end - start

                data = content  # Assuming content is already in the desired format

                run = self.create_run_with_results(
                    experiment=experiment,
                    configured_model=configured_model,
                    elapsed_time=elapsed,
                    output_data=data,
                )
                results.append({
                    "run_id": run.id,
                    "elapsed_time": elapsed,
                })
            return results
        else:
            raise NotImplementedError(f"Provider {llm_model.provider} not supported yet.")

    def create_run_with_results(self, experiment, configured_model, elapsed_time, output_data):
        data = json.loads(output_data)

        # Create Run instance
        run = Run.objects.create(
            experiment=experiment,
            configured_model=configured_model,
            elapsed_time=elapsed_time,
        )

        # Process output_data to create MobileApp and MobileAppRanked entries
        apps_names = data.get('a', [])
        for idx, app_name in enumerate(apps_names, start=1):
            mobile_app, created = MobileApp.objects.get_or_create(name=app_name)
            MobileAppRanked.objects.create(
                mobile_app=mobile_app,
                run=run,
                rank=idx
            )
        
        # Ranking criteria processing (if any)
        criteria_list = data.get('c', [])
        for criterion in criteria_list:
            RankingCriteria.objects.create(
                name=criterion.get('n', 'Unnamed Criterion'),
                description=criterion.get('d', ''),
                run=run
            )

        return run

class MobileAppViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MobileApp.objects.all()
    serializer_class = MobileAppSerializer

class RankingCriteriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RankingCriteria.objects.all()
    serializer_class = RankingCriteriaSerializer
