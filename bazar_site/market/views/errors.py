"""
Обработчики HTTP-ошибок (400, 403, 404, 500).
"""

from django.shortcuts import render

from ._helpers import _get_site_settings_context


def error_400(request, exception):
    context = _get_site_settings_context()
    context["message"] = "Некорректный запрос (ошибка 400)."
    return render(request, "400.html", context, status=400)


def error_403(request, exception):
    context = _get_site_settings_context()
    context["message"] = "У вас нет прав для выполнения этого действия (ошибка 403)."
    return render(request, "403.html", context, status=403)


def error_404(request, exception):
    context = _get_site_settings_context()
    context["message"] = "Страница не найдена или была удалена (ошибка 404)."
    return render(request, "404.html", context, status=404)


def error_500(request):
    context = _get_site_settings_context()
    context["message"] = "На сервере произошла ошибка (ошибка 500). Мы уже работаем над этим."
    return render(request, "500.html", context, status=500)
