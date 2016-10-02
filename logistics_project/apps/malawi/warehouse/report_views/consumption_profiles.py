from datetime import datetime

from django.db.models import Sum

from dimagi.utils.dates import first_of_next_month, delta_secs, months_between,\
    secs_to_days

from logistics.models import SupplyPoint, Product
from static.malawi import config

from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.warehouse.models import CalculatedConsumption
from logistics_project.apps.malawi.warehouse.report_utils import get_consumption_chart
from logistics_project.apps.malawi.util import get_default_supply_point,\
    fmt_or_none, hsa_supply_points_below, is_country, is_district,\
    is_facility


def consumption_row(sp, p, datespan):
    relevant = CalculatedConsumption.objects.filter(supply_point=sp, product=p,
                                                    date__gte=datespan.startdate,
                                                    date__lte=datespan.enddate)
    now = datetime.utcnow()
    end = now if datespan.enddate.year == now.year and \
                 datespan.enddate.month == now.month \
              else first_of_next_month(datespan.enddate)
    
    vals = relevant.aggregate(Sum('calculated_consumption'), 
                              Sum('time_stocked_out'),
                              Sum('time_with_data'),
                              Sum('time_needing_data'))
    tot_cons = vals['calculated_consumption__sum'] or 0
    tot_so_time = vals['time_stocked_out__sum'] or 0
    tot_time_with_data = vals['time_with_data__sum'] or 0
    tot_time_needing_data = vals['time_needing_data__sum'] or 0

    avg_so_time = 0
    if relevant.count() > 0:
        if relevant[0].total:
            num_hsas = relevant[0].total
            avg_so_time = tot_so_time / num_hsas

    period_secs = delta_secs(end - datespan.startdate)
    assert period_secs >= avg_so_time
    adjusted_secs = period_secs - avg_so_time
    so_adjusted_cons = (tot_cons * (period_secs / adjusted_secs)) if adjusted_secs else 0 
    
    scale_factor = float(tot_time_with_data) / float(tot_time_needing_data) \
         if tot_time_needing_data != 0 else 0
    data_adjusted_cons = so_adjusted_cons / scale_factor \
        if scale_factor != 0 else so_adjusted_cons 
    amc = data_adjusted_cons / len(months_between(datespan.startdate,
                                                  datespan.enddate))
    _f = lambda x: fmt_or_none(x, percent=False)
    _f2 = lambda x: fmt_or_none(x * 100., percent=True)
    return [p.name, tot_cons, _f(secs_to_days(avg_so_time)), 
            _f(so_adjusted_cons), _f2(scale_factor), 
            _f(data_adjusted_cons), _f(amc)]



class View(warehouse_view.DistrictOnlyView):

    def get_consumption_profile_table_headers(self, request):
        base_level_description_plural = config.BaseLevel.get_base_level_description(request.base_level, plural=True)
        return [
            "Product",
            "Total Actual Consumption for selected period",
            "# stockout days for all %s" % base_level_description_plural,
            "Total consumption adjusted for stockouts",
            "Data coverage (% of period)",
            "Total consumption (adjusted  for stockouts and data coverage)",
            "AMC for all %s" % base_level_description_plural,
        ]

    def get_consumption_profile_table(self, request, supply_point, extra_table_params=None):
        extra_table_params = extra_table_params or {}
        table = {
            "is_datatable": False,
            "is_downloadable": True,
            "header": self.get_consumption_profile_table_headers(request),
            "data": [
                consumption_row(supply_point, p, request.datespan)
                for p in Product.objects.filter(type__base_level=request.base_level)
            ],
        }
        table.update(extra_table_params)
        return table

    def get_reporting_location_type(self, request, supply_point):
        if request.base_level_is_hsa:
            if is_country(supply_point):
                location_type = "national"
            elif is_district(supply_point):
                location_type = "district"
            elif is_facility(reporting_supply_point):
                location_type = "facility"
            else:
                raise config.BaseLevel.InvalidReportingSupplyPointException(supply_point.code)
        elif request.base_level_is_facility:
            if is_country(supply_point):
                location_type = "national"
            elif is_district(supply_point):
                location_type = "district"
            else:
                raise config.BaseLevel.InvalidReportingSupplyPointException(supply_point.code)
        else:
            raise config.BaseLevel.InvalidBaseLevelException(supply_point.code)

        return location_type

    def custom_context(self, request):
        reporting_supply_point = self.get_reporting_supply_point(request)
        
        hsa_list = selected_hsa = hsa_table = None
        
        if is_facility(reporting_supply_point):
            hsa_list = hsa_supply_points_below(reporting_supply_point.location)
            hsa_id = request.GET.get("hsa", "")
            if hsa_id:
                selected_hsa = SupplyPoint.objects.get(code=hsa_id) 
                hsa_table = self.get_consumption_profile_table(
                    request,
                    selected_hsa,
                    {"id": "hsa-consumption-profiles"}
                )

        reporting_location_consumption_profile_table = self.get_consumption_profile_table(
            request,
            reporting_supply_point,
            {
                "id": "location-consumption-profiles",
                "location_type": self.get_reporting_location_type(request, reporting_supply_point),
            }
        )

        p_code = request.REQUEST.get("product", "")
        
        p = Product.objects.get(sms_code=p_code) if p_code else Product.objects.all()[0]
        amc_table, line_chart = get_consumption_chart(reporting_supply_point, p, request.datespan.startdate,
                                                      request.datespan.enddate)
        return {
            "location_table": reporting_location_consumption_profile_table,
            "hsa_table": hsa_table,
            "hsa_list": hsa_list,
            "selected_hsa": selected_hsa,
            "amc_mos_table": amc_table,
            "line_chart": line_chart,
            "selected_product": p
        }
