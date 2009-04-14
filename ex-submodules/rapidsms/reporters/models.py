#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models
import os

# load the rapidsms configuration, for BackendManager
# to check which backends are currently running
from rapidsms.config import Config
conf = Config(os.environ["RAPIDSMS_INI"])


class Reporter(models.Model):
    """This model represents a KNOWN person, that can be identified via
       their alias and/or connection(s). Unlike the RapidSMS Person class,
       it should not be used to represent unknown reporters, since that
       could lead to multiple objects for the same "person". Usually, this
       model should be created through the WebUI, in advance of the reporter
       using the system - but there are always exceptions to these rules..."""
    first_name = models.CharField(max_length=30, blank=True)
    last_name  = models.CharField(max_length=30, blank=True)
    alias      = models.CharField(max_length=20, unique=True)
	
    class Meta:
        ordering = ["last_name", "first_name"]
    
    # the string version of report
    # now contains only their name
    def __unicode__(self):
        return "%s %s" % (
            self.first_name,
            self.last_name)
    
    def connection(self):
        """Returns the connection object last used by this Reporter.
           The field is (probably) updated by app.py when receiving
           a message, so depends on _incoming_ messages only."""
        
        # TODO: add a "preferred" flag to connection, which then
        # overrides the last_seen connection as the default, here
        return self.connections.latest("last_seen")

    def last_seen(self):
        """Returns the Python datetime that this Reporter was last seen,
           on any Connection. Before displaying in the WebUI, the output
           should be run through the XXX  filter, to make it prettier."""
        
        # comprehend a list of datetimes that this
        # reporter was last seen on each connection,
        # excluding those that have never seen them
        timedates = [
            c.last_seen
            for c in self.connections.all()
            if c.last_seen is not None]
        
        # return the latest, or none, if they've
        # has never been seen on ANY connection
        return max(timedates) if timedates else None


class RecursiveManager(models.Manager):
    """Provides a method to flatten a recursive model (a model which has a ForeignKey field linked back
       to itself), in addition to the usual models.Manager methods. This Manager queries the database
       only once (unlike select_related), and sorts them in-memory. Obivously, this efficiency comes
       at the cost much higher CPU usage."""
    
    def flatten(self, via_field="parent_id"):
        all_objects = list(self.model.objects.all())
        
        def pluck(pk=None, depth=0):
            output = []
            
            for object in all_objects:
                print getattr(object, via_field)
                if getattr(object, via_field) == pk:
                    output += [object] + pluck(object, depth+1)
                    object.depth = depth
            
            return output
        return pluck()


class ReporterGroup(models.Model):
    title       = models.CharField(max_length=30, unique=True)
    parent      = models.ForeignKey("self", related_name="children", null=True, blank=True)
    description = models.TextField(blank=True)
    objects     = RecursiveManager()
    
    class Meta:
        verbose_name = "Group"

    def __unicode__(self):
        return self.title
    
    def flat_children(self):
        return [self] + [c.flat_children() for c in self.children.all()]
        
    @classmethod
    def flat_tree(klass):
        return [g.flat_children() for g in klass.objects.filter(parent=None)]


class BackendManager(models.Manager):
    def get_query_set(self):
        
        # fetch a list of all the backends
        # that we already have objects for
        known_backends  = PersistantBackend.raw_objects.values_list("title", flat=True)
        
        # and a list of the backends which are
        # running, which we SHOULD have objects for 
        running_backends = [be["title"] for be in conf["rapidsms"]["backends"]]
        
        # find any running backends which currently
        # don't have objects, and fill in the gaps
        for t in running_backends:
            if not t in known_backends:
                PersistantBackend(title=t).save()
        
        # now that we're sure the backends table is up
        # to date, continue fetching the queryset as usual
        return super(BackendManager, self).get_query_set()


class PersistantBackend(models.Model):
    """This class exists to provide a primary key for each
       named RapidSMS backend, which can be linked from the
       other modules. We can't use a char field with OPTIONS
       (in models which wish to link to a backend), since the
       available backends (and their orders) may change after
       deployment; hence, something persistant is needed."""
    title       = models.CharField(max_length=30, unique=True)
    raw_objects = models.Manager()
    objects     = BackendManager()
    
    class Meta:
        verbose_name = "Backend"
    
    def __unicode__(self):
        return self.title


class PersistantConnection(models.Model):
    """This class is a persistant version of the RapidSMS Connection
       class, to keep track of the various channels of communication
       that Reporters use to interact with RapidSMS (as a backend +
       identity pair, like rapidsms.connection.Connection). When a
       Reporter is seen communicating via a new backend, or is expected
       to do so in future, a PersistantConnection should be created,
       so they can be recognized by their backend + identity pair."""
    backend   = models.ForeignKey(PersistantBackend, related_name="connections")
    identity  = models.CharField(max_length=30)
    reporter  = models.ForeignKey(Reporter, related_name="connections")
    last_seen = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Connection"
    
    def __unicode__(self):
        return "%s:%s" % (
            self.backend,
            self.identity)
    
    def prefer(self):
        """Removes the _preferred_ flag from all other PersistantConnection objects
           linked to the same Reporter, and sets the _preferred_ flag on this object."""
        for pc in PersistantConnection.objects.filter(reporter=self.reporter):
            pc.preferred = True if pc == self else False
            pc.save()
