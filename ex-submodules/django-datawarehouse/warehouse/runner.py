

class WarehouseRunner(object):
    """
    This class gets executed by the warehouse management command.
    Subclasses control how data gets into the warehouse.
    """
    
    def cleanup(self, start, end):
        """
        Cleanup all warehouse data between start and end.
        """
        pass
    
    def generate(self, start, end):
        """
        Generate all warehouse data between start and end.
        """
        pass
    
class DemoWarehouseRunner(WarehouseRunner):
    """
    A reference implementation of the warehouse runner. Your subclasses
    should probably do more than this.
    """
    
    def cleanup(self, start, end):
        print ("Demo warehouse cleanup! Would clean all data from %s-%s. "
               "Override WAREHOUSE_CLASS in your settings.py file to have "
               "this actually do something.") 
    
    def generate(self, start, end):
        print ("Demo warehouse generate! Would create all data from %s-%s. "
               "Override WAREHOUSE_CLASS in your settings.py file to have "
               "this actually do something.") % (start, end)
    
    
