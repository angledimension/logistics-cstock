#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseServerError
from django.template import RequestContext
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.shortcuts import get_object_or_404
from django.db import IntegrityError, transaction

from rapidsms.webui.utils import *
from apps.reporters.models import *
from apps.reporters.utils import *


def message(req, msg, link=None):
    return render_to_response(req,
        "message.html", {
            "message": msg,
            "link": link
    })


@require_GET
def index(req):
    data = { }
    
    
    # in the left panel, render the reporters
    # index or the add/edit a group form
#    if "group" in req.GET:
#        if req.GET["group"] != "new":
#            data["group"] = get_object_or_404(ReporterGroup, pk=req.GET["group"])
#        else:
#            data["add_group"] = 1
#    else:
#        data["reporters"] = paginated(req, Reporter.objects.all())
    
    
    # in the right panel, render the groups
    # index, or the add/edit a reporter form
#    if "reporter" in req.GET:
#        if req.GET["reporter"] != "new":
#            data["reporter"] = get_object_or_404(Reporter, pk=req.GET["reporter"])
#        else:
#            data["add_reporter"] = 1
#    else:
#        data["groups"] = paginated(req, ReporterGroup.objects.all())
    
    return render_to_response(req,
        "reporters/index.html", {
        "reporters": paginated(req, Reporter.objects.all()),
        "groups": paginated(req, ReporterGroup.objects.flatten()),
    })


def check_reporter_form(req):
    
    # verify that all non-blank
    # fields were provided
    missing = [
        field.verbose_name
        for field in Reporter._meta.fields
        if req.POST.get(field.name, "") == ""
           and field.blank == False]
    
    # TODO: add other validation checks,
    # or integrate proper django forms
    return {
        "missing": missing }


def update_reporter(req, rep):
    
    # as default, we will delete all of the connections
    # and groups from this reporter. the loops will drop
    # objects that we SHOULD NOT DELETE from these lists
    del_conns = list(rep.connections.values_list("pk", flat=True))
    del_grps = list(rep.groups.values_list("pk", flat=True))


    # iterate each of the connection widgets from the form,
    # to make sure each of them are linked to the reporter
    connections = field_bundles(req.POST, "conn-backend", "conn-identity")
    for be_id, identity in connections:
        
        # skip this pair if either are missing
        if not be_id or not identity:
            continue
        
        # create the new connection - this could still
        # raise a DoesNotExist (if the be_id is invalid),
        # or an IntegrityError or ValidationError (if the
        # identity or report is invalid)
        conn, created = PersistantConnection.objects.get_or_create(
            backend=PersistantBackend.objects.get(pk=be_id),
            identity=identity,
            reporter=rep)
        
        # if this conn was already
        # linked, don't delete it!
        if conn.pk in del_conns:
            del_conns.remove(conn.pk)


    # likewise for the group objects
    groups = field_bundles(req.POST, "group")	
    for grp_id, in groups:
        
        # skip this group if it's empty
        # (an empty widget is displayed as
        # default, which may be ignored here)
        if not grp_id:
            continue
        
        # link this group to the reporter
        grp = ReporterGroup.objects.get(pk=grp_id)
        rep.groups.add(grp)
        
        # if this group was already
        # linked, don't delete it!
        if grp.pk in del_grps:
            del_grps.remove(grp.pk)
    
    
    # delete all of the connections and groups 
    # which were NOT in the form we just received
    rep.connections.filter(pk__in=del_conns).delete()
    rep.groups.filter(pk__in=del_grps).delete()


@require_http_methods(["GET", "POST"])
def add_reporter(req):
    def get(req):
        return render_to_response(req,
            "reporters/reporter.html", {
            "reporters": paginated(req, Reporter.objects.all()) })

    @transaction.commit_manually
    def post(req):
        
        # check the form for errors
        errors = check_reporter_form(req)
        
        # if any fields were missing, abort. this is
        # the only server-side check we're doing, for
        # now, since we're not using django forms here
        if errors["missing"]:
            transaction.rollback()
            return message(req,
                "Missing Field(s): %s" %
                    ", ".join(missing),
                link="/reporters/add")
        
        try:
            # create the reporter object from the form
            rep = insert_via_querydict(Reporter, req.POST)
            rep.save()
            
            # every was created, so really
            # save the changes to the db
            update_reporter(req, rep)
            transaction.commit()
            
            # full-page notification
            return message(req,
                "Reporter %d added" % (rep.pk),
                link="/reporters")
        
        except Exception, err:
            transaction.rollback()
            raise
    
    # invoke the correct function...
    # this should be abstracted away
    if   req.method == "GET":  return get(req)
    elif req.method == "POST": return post(req)


@require_http_methods(["GET", "POST"])  
def edit_reporter(req, pk):
    rep = get_object_or_404(Reporter, pk=pk)
    
    def get(req):
        return render_to_response(req,
            "reporters/reporter.html", {
            "reporters": paginated(req, Reporter.objects.all()),
            "all_groups": ReporterGroup.objects.flatten(),
            "connections": rep.connections.all(),
            "groups": rep.groups.all(),
            "reporter": rep })
    
    @transaction.commit_manually
    def post(req):
        
        # if DELETE was clicked... delete
        # the object, then and redirect
        if req.POST.get("delete", ""):
            pk = rep.pk
            rep.delete()
            
            transaction.commit()
            return message(req,
                "Reporter %d deleted" % (pk),
                link="/reporters")
                
        else:
            # check the form for errors (just
            # missing fields, for the time being)
            errors = check_reporter_form(req)
            
            # if any fields were missing, abort. this is
            # the only server-side check we're doing, for
            # now, since we're not using django forms here
            if errors["missing"]:
                transaction.rollback()
                return message(req,
                    "Missing Field(s): %s" %
                        ", ".join(errors["missing"]),
                    link="/reporters/%s" % (rep.pk))
            
            try:
                # automagically update the fields of the
                # reporter object, from the form
                update_via_querydict(rep, req.POST).save()
                update_reporter(req, rep)
                
                # no exceptions, so no problems
                # commit everything to the db
                transaction.commit()
                
                # full-page notification
                return message(req,
                    "Reporter %d updated" % (rep.pk),
                    link="/reporters")
            
            except Exception, err:
                transaction.rollback()
                raise
        
    # invoke the correct function...
    # this should be abstracted away
    if   req.method == "GET":  return get(req)
    elif req.method == "POST": return post(req)


@require_http_methods(["GET", "POST"])
def add_group(req):
    if req.method == "GET":
        return render_to_response(req,
            "reporters/group.html", {
                "all_groups": ReporterGroup.objects.flatten(),
                "groups": paginated(req, ReporterGroup.objects.flatten()) })
        
    elif req.method == "POST":
        
        # create a new group using the flat fields,
        # then resolve and update the parent group
        # TODO: resolve foreign keys in i_via_q
        grp = insert_via_querydict(ReporterGroup, req.POST)
        parent_id = req.POST.get("parent_id", "")
        if parent_id:
            grp.parent = get_object_or_404(
                ReporterGroup, pk=parent_id)
        
        grp.save()
        
        return message(req,
            "Group %d added" % (grp.pk),
            link="/reporters")


@require_http_methods(["GET", "POST"])
def edit_group(req, pk):
    grp = get_object_or_404(ReporterGroup, pk=pk)
    
    if req.method == "GET":
        return render_to_response(req,
            "reporters/group.html", {
                "all_groups": ReporterGroup.objects.flatten(),
                "groups": paginated(req, ReporterGroup.objects.flatten()),
                "group": grp })
    
    elif req.method == "POST":
        # if DELETE was clicked... delete
        # the object, then and redirect
        if req.POST.get("delete", ""):
            pk = grp.pk
            grp.delete()
            
            return message(req,
                "Group %d deleted" % (pk),
                link="/reporters")

        # otherwise, update the flat fields of the group
        # object, then resolve and update the parent group
        # TODO: resolve foreign keys in u_via_q
        else:
            update_via_querydict(grp, req.POST)
            parent_id = req.POST.get("parent_id", "")
            if parent_id:
                grp.parent = get_object_or_404(
                    ReporterGroup, pk=parent_id)
            
            # if no parent_id was passed, we can assume
            # that the field was cleared, and remove it
            else: grp.parent = None
            grp.save()
            
            return message(req,
                "Group %d saved" % (grp.pk),
                link="/reporters")
