from collections import defaultdict

from django import template

from ..models import FooterLink, FooterSocialLink, SiteSettings

register = template.Library()


@register.inclusion_tag("market/_footer.html", takes_context=True)
def render_footer(context):
    site_settings = context.get("site_settings")
    if site_settings is None:
        site_settings = SiteSettings.objects.first()

    links = FooterLink.objects.filter(is_active=True).order_by(
        "column", "sort_order", "title"
    )
    socials = FooterSocialLink.objects.filter(is_active=True).order_by("sort_order")

    columns: dict[int, list[FooterLink]] = defaultdict(list)
    for link in links:
        columns[link.column].append(link)

    return {
        "site_settings": site_settings,
        "footer_columns": columns,
        "footer_socials": socials,
    }

