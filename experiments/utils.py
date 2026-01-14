from jinja2 import Template as JinjaTemplate

def render_user_prompt_for_feature(user_prompt, feature, k=None):
    """
    Renderiza el texto del user_prompt sustituyendo la variable 'feature'
    (y opcionalmente 'k') usando Jinja2.
    """
    # Convertir primera letra a minúscula si es mayúscula
    feature_name = feature.name
    if feature_name and feature_name[0].isupper():
        feature_name = feature_name[0].lower() + feature_name[1:]
    
    context = {
        "feature": feature_name,
    }
    if k is not None:
        context["k"] = k
    return JinjaTemplate(user_prompt.text).render(**context)
