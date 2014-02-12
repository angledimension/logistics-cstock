from django import template
from django.core.exceptions import ObjectDoesNotExist
from logistics.models import SupplyPoint
from logistics.templatetags.logistics_report_tags import r_2_s_helper
from logistics_project.apps.malawi.warehouse.report_utils import WarehouseProductAvailabilitySummary
from logistics_project.apps.malawi.util import get_country_sp

register = template.Library()

@register.simple_tag
def warehouse_product_availability_summary(location, date, width=900, height=300):
    sp = SupplyPoint.objects.get(location=location) if location else get_country_sp()
    try:
        summary = WarehouseProductAvailabilitySummary(sp, date, width, height)
        return r_2_s_helper("logistics/partials/product_availability_summary.html",
                             {"summary": summary})
    except ObjectDoesNotExist:
        return '<p class="error">Sorry, no data found for chart</p>'

@register.filter
def is_district_user(user):
    return user.is_superuser or user.groups.filter(name='district').count()
