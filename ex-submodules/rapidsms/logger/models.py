#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import django
from django.db import models
from apps.nodegraph.models import NodeSet

MAX_LATIN_SMS_LEN = 160 

class MessageBase(models.Model):
    text = models.CharField(max_length=MAX_LATIN_SMS_LEN)
    # TODO save connection title rather than wacky object string?
    identity = models.CharField(max_length=150)
    backend = models.CharField(max_length=150)
    # this isn't modular
    # but it's optional and saves some ridiculous querying for smsforum frontpage
    # TODO save domain to wacky object string rather than connection title?
    # (to reduce app dependencies)
    domain = models.ForeignKey(NodeSet,null=True)
    
    def __unicode__(self):
        return u'%s (%s) %s' % (self.identity, self.backend, self.text)
    
    class Meta:
        abstract = True
    
    
    
class IncomingMessage(MessageBase):
    received = models.DateTimeField(auto_now_add=True)
    
    # Helper methods to allow this object to be treated similar
    # to the outgoing message, e.g. if they are in the same list
    # in a template
    @property
    def date(self):
        '''Same as received''' 
        return self.received
    
    def is_incoming(self):
        return True
    
    def __unicode__(self):
        return u"%s %s" % (MessageBase.__unicode__(self), self.received)

    class Meta:
        # the permission required for this tab to display in the UI
        permissions = (
            ("can_view", "Can view message logs"),
        )
    
class OutgoingMessage(MessageBase):
    sent = models.DateTimeField(auto_now_add=True)
    
    @property
    def date(self):
        '''Same as sent''' 
        return self.sent
    
    def is_incoming(self):
        return False
    
    def __unicode__(self):
        return u"%s %s" % (MessageBase.__unicode__(self), self.sent)

class CodeSet(models.Model):
    """
    An arbitrary set of codes with which messages can be tagged.
    e.g. category, state, flagged
    """
    name = models.CharField(max_length = 64, unique=True) 
    
    def __unicode__(self):
        return unicode(self.name)

class Code(models.Model):
    """
    This model holds codes which can be mapped to individual messages
    e.g. good/bad/ignore, open/inprogress/closed, flagged/not_flagged
    """
    set = models.ForeignKey(CodeSet, null=False)
    name = models.CharField(max_length = 64, unique=True) # e.g. sante, les droits humain, etc.
    slug = models.CharField(max_length = 8, unique=True) # e.g. san, dro, etc.
    
    def __unicode__(self):
        return u"%(name)s" % { 'name':self.name }

class MessageTag(models.Model):
    """
    A dynamic way of associating messages with codes without requiring that
    all messages be coded
    """
    message = models.ForeignKey(IncomingMessage)
    code = models.ForeignKey(Code)

    def __unicode__(self):
        return u"%(message)s: %(tag)s" % { 'message':self.message, 'tag':self.code }

class MessageAnnotation(models.Model):
    """
    A dynamic way of associating messages with free-form annotations
    without requiring that all messages be annotated
    """
    message = models.ForeignKey(IncomingMessage)
    text = models.CharField(max_length=255,blank=True)

    def __unicode__(self):
        return u"%(message)s: %(annotation)s" % { 'message':self.message, 'annotation':self.annotation }


