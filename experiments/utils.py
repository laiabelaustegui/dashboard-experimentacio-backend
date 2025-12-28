from jinja2 import Template as JinjaTemplate

def render_user_prompt_for_feature(user_prompt, feature, k=None):
    """
    Renderiza el texto del user_prompt sustituyendo la variable 'feature'
    (y opcionalmente 'k') usando Jinja2.
    """
    context = {
        "feature": feature.name,
    }
    if k is not None:
        context["k"] = k
    return JinjaTemplate(user_prompt.text).render(**context)
