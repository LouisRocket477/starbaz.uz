from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden

from ..site.services import get_site_settings
from ..support.models import SupportRequest, SupportMessage


@login_required
def support_reply(request, pk: int):
    """Ответ пользователя в уже созданном тикете + скриншот.

    После закрытия тикета (is_resolved = True) новые ответы не принимаются.
    """
    support_request = get_object_or_404(SupportRequest, pk=pk)

    # Разрешаем отвечать только автору тикета.
    if support_request.author_id != request.user.id:
        return HttpResponseForbidden("Недостаточно прав для этого тикета.")

    if support_request.is_closed or request.method != "POST":
        return redirect("market:support_my")

    text = (request.POST.get("reply_message") or "").strip()
    screenshot = request.FILES.get("reply_screenshot")

    if not text and not screenshot:
        return redirect("market:support_my")

    SupportMessage.objects.create(
        request=support_request,
        author=request.user,
        text=text,
        screenshot=screenshot,
    )

    return redirect("market:support_my")

