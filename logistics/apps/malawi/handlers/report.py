from logistics.apps.logistics.models import ProductReportsHelper, StockRequest,\
    ContactRole
from django.utils.translation import ugettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.decorators import logistics_contact_and_permission_required
from logistics.apps.logistics.util import config
from logistics.apps.malawi import util
from logistics.apps.malawi.shortcuts import create_stock_report,\
    send_emergency_responses, send_soh_responses

class ReportRegistrationHandler(KeywordHandler):
    """
    Report stock on hand or a receipt for someone else
    """
    
    keyword = "report"
    
    def help(self):
        self.respond(_(config.Messages.REPORT_HELP))
        
    
    @logistics_contact_and_permission_required(config.Operations.REPORT_FOR_OTHERS)
    def handle(self, text):
    
        words = text.split(" ")
        if len(words) < 2:
            return self.help()
        
        hsa_id = words[0]
        keyword = words[1].lower()
        self.report_data = " ".join(words[2:])
        self.hsa = util.get_hsa(hsa_id)
        if self.hsa is None:
            self.respond(config.Messages.UNKNOWN_HSA, hsa_id=hsa_id)
        elif keyword not in [Reports.SOH, Reports.REC, Reports.EMERGENCY_SOH]:
            self.respond(config.Messages.BAD_REPORT_KEYWORD, keyword=hsa_id)
        else:
            # we've got an hsa, we've got a keyword, let's rock 
            # clarity over DRY
            if keyword == Reports.SOH:
                self._process_soh()
            elif keyword == Reports.EMERGENCY_SOH:
                self._process_emergency_soh()
            elif keyword == Reports.REC:
                self._process_rec()
            elif keyword == Reports.GIVE: # not yet possible given the above
                self._process_give()
            
    def _process_soh(self):
        stock_report = create_stock_report(Reports.SOH,  
                                           self.hsa.supply_point,
                                           self.report_data, 
                                           self.msg.logger_msg)
        requests = StockRequest.create_from_report(stock_report, self.hsa)
        if stock_report.errors:
            # TODO: respond better.
            self.respond(config.Messages.GENERIC_ERROR)
        else:
            if self.msg.logistics_contact.role == ContactRole.objects.get(code=config.Roles.IN_CHARGE):
                self.respond(config.Messages.REPORT_SOH_RESPONSE,
                             hsa=self.hsa.name,
                             products=", ".join(req.sms_format() for req in requests),
                             hsa_id=self.hsa.supply_point.code)
            else:
                assert(self.msg.logistics_contact.role == ContactRole.objects.get(code=config.Roles.HSA))
                send_soh_responses(self.msg, stock_report, requests)
                
    def _process_emergency_soh(self):
        stock_report = create_stock_report(Reports.EMERGENCY_SOH,  
                                           self.hsa.supply_point,
                                           self.report_data, 
                                           self.msg.logger_msg)
        requests = StockRequest.create_from_report(stock_report, self.hsa)
        if stock_report.errors:
            # TODO: respond better.
            self.respond(config.Messages.GENERIC_ERROR)
        else:
            if self.msg.logistics_contact.role == ContactRole.objects.get(code=config.Roles.IN_CHARGE):
                self.respond(config.Messages.REPORT_SOH_RESPONSE,
                         hsa=self.hsa.name,
                         products=", ".join(req.sms_format() for req in requests),
                         hsa_id=self.hsa.supply_point.code)
            else:
                assert(self.msg.logistics_contact.role == ContactRole.objects.get(code=config.Roles.HSA))
                send_emergency_responses(self.msg, stock_report, requests)
            
    def _process_rec(self):
        stock_report = create_stock_report(Reports.REC,  
                                           self.hsa.supply_point,
                                           self.report_data, 
                                           self.msg.logger_msg)
        requests = StockRequest.close_pending_from_receipt_report(stock_report, self.hsa)
        if stock_report.errors:
            # TODO: respond better.
            self.respond(config.Messages.GENERIC_ERROR)
        else:
            self.respond(config.Messages.REPORT_RECEIPT_RESPONSE, 
                         reporter=self.msg.logistics_contact.name,
                         hsa=self.hsa.name,
                         products=" ".join(stock_report.reported_products()).strip())

    def _process_give(self):
        raise NotImplemented("stop that!")