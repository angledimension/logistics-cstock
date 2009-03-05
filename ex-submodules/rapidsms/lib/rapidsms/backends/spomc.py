#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from backend import Backend
import spomsky


class Spomc(Backend):
    
    def __init__(self, router, host="localhost", port="8100"):
        self.client = spomsky.Client(host, port)
        super(Backend,self).__init_(router)

    def start(self):
        #bare minimum to pass test
        pass

    def stop(self):
        #bare minimum to pass test
        pass

    def send(self,message):
        #bare minimum to pass test
        pass

    def receive(self, number, message):
        #bare minimum to pass test
        self.router.messages.append(message)
