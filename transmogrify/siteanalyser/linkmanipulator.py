"""
    
       Fix links in incoming HTML content using transmogrifier
       
"""

import urllib
import lxml
import logging

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultMatcher

logger = logging.getLogger("linkmanipulator")

class BadOptionException(RuntimeError):
    """ This is raised if the section blueprint is improperly configured """
    pass

class LinkManipulator(object):
    """    
    
    Parameters:
    
        * extensions: space separated list of link extensions to remove
        
        * fields: List of transmogrifier fields where the blueprint is applied
    
        * relative-only: Apply blueprint for relative links only
    
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    
    def __init__(self, transmogrifier, name, options, previous):
        """ Initialize section blueprint.
        
        @param transmogrifier:  collective.transmogrifier.transmogrifier.Transmogrifier instance
        
        @param name: Section name as given in the blueprint
        
        @param previous: Prior blueprint in the chain. A Python generator object.
        
        @param options: Options as a dictionary as they appear in pipeline.cfg. Parsed INI format.    
        """    
        
        # Initialize common class attributes
        self.name = name
        self.previous = previous
        self.context = transmogrifier.context
        
        self.readOptions(options)
        
    def readOptions(self, options):
        """ Read options give in pipeline.cfg. 
        
        Initialize all parameters to None if they are not present.
        Then the options can be safely checked in checkOptions() method.
        """
        
        # Remote site / object URL containing HTTP Basic Auth username and password 
        self.extensions = options.get("extensions", "").split(" ") 
        self.fields = options.get("fields", "").split(" ")
        self.relative_only = options.get("relative-only", "false")
    
        self.relative_only = self.relative_only == "true"
    
    def checkOptions(self):
        """ See that all necessary options have been set-up.
        
        Note that we might want to modify the blueprint section
        instance attributes in run-time e.g. for setting the remote
        site URL and auth information, so we should not yet call checkOptions()
        during the construction.
        """
        if not self.extensions:
            raise BadOptionException("extensions parameter missing")

        if not self.fields:
            raise BadOptionException("Fields name missings")

    
    def fixLink(self, a):
        """
        @param a: lxml node
        """
        

        href = a.attrib["href"]
        
        if href.startswith("http"):
            # match http + https
            if self.relative_only:
                return
        
        for extension in self.extensions:
            # The link might 
            if href.endswith(extension):
                logger.debug("Fixing link " + href)
                href = href[0:-len(extension)]
                
        a.attrib["href"] = href
        
    def walk(self, html):
        """
        Parse HTML in lxml and modify links
        """
        
        try:
            dom = lxml.html.fromstring(html)
        except Exception, e:
            print "Encountered bad html:" + str(html)
            raise e
        
        links = dom.iter("a")
        for a in links:
            if "href" in a.attrib:
                self.fixLink(a)

        return lxml.html.tostring(dom)
    
        
    def __iter__(self):
        """
        Run transmogrify pipeline 
        """
        self.checkOptions()
                            
        for item in self.previous:
            
            keys = item.keys()
            
            if "_bad_url" in keys:
                # This item was not propely crawled
                continue
        
    
            for field in self.fields:
                if field in keys:
                    # Extract iterated item field
                    payload = item[field]
                    item[field] = self.walk(payload)
                    
            yield item