'''
Created on Oct 6, 2011

@author: tim
'''
from django.shortcuts import render_to_response, HttpResponse
from django.core.context_processors import csrf
from django.core import serializers 
from django.utils import simplejson
from django.template import RequestContext

from discorrelate.forms import requestForm

from json import JSONEncoder
#import discogs_client as discogsAPI
import re
    
def getQuery(apiKey, dataset, query):
    import httplib2
    import urllib
    h = httplib2.Http(".cache")
    baseURL = "http://api.kasabi.com/dataset/%s/apis/sparql?" % dataset
    params = urllib.urlencode({'apikey':apiKey, 'query':query, 'output':'json'})
    response, content = h.request(baseURL+params)
    if response.status in range(200,300):
        import simplejson as json
        return json.loads(content)
    else:
        print "Oh no! %d %s " % (response.status, response.reason)
        return False

def flatten(results):
    nodes, links = [], []
    nodesLookup = {} # A dictionary to lookup which nodes have already been encountered
    linksLookup = {} # Dictionary of tuples where (linkStart,linkFinish) 
    for subject in results:
        if not subject in nodesLookup:
            nodesLookup[subject] = len(nodes)
            nodes.append({}) # add blank node, will fill with properties later
        for predicate in results[subject]:
            if predicate == 'http://data.rewire.it#linked':
                # this predicate has been reserved to specify links
                objects = results[subject][predicate]
                for object in objects:
                    if not object['value'] in nodesLookup:
                        nodesLookup[object['value']] = len(nodes)
                        nodes.append({}) # add blank node, will fill with properties later
                        
                    # now add the links
                    linkStart = nodesLookup[subject]
                    linkEnd =  nodesLookup[object['value']]
                    link = (linkStart, linkEnd)
                    if not link in links:
                        linksLookup[link] = len(links)
                        links.append({'source':linkStart,'target':linkEnd,'value':1})
                    else:
                        newValue = links[linksLookup[link]]['value']+1
                        links[linksLookup[link]]['value'] = newValue
            else:
                # any predicate not specified as a link is added to the node as a property
                
                #get last bit of URL to use as property name (bit after the last / or #)
                splits = re.split(r'[/|#]', predicate)
                propName = splits[len(splits)-1]
                objects = results[subject][predicate]
                for object in objects:
                    nodes[nodesLookup[subject]][propName] = object['value']
            
    return simplejson.dumps({'nodes':nodes,'links':links})

def root(request):
    if not request.POST:
        form = requestForm()
        c = RequestContext(request, {'form':form})
        c.update(csrf(request))
        return render_to_response('root.html',c)
    url = request.POST.get('url')
    year = request.POST.get('year')
    #query = request.POST.get('query')
    
    
    q="""
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
      PREFIX mo: <http://purl.org/ontology/mo/>
      PREFIX dateIssued: <http://purl.org/dc/terms/issued>
      PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
      PREFIX dc: <http://purl.org/dc/terms/>
      PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    
      PREFIX INPUT: <%(url)s>
      
      CONSTRUCT{
        ?NODEartist1 <http://data.rewire.it#linked> ?NODErelease1;
                        foaf:name ?artist1Name;
                        mo:discogs ?artist1Discogs;
                        rdf:type ?artist1Type.
                        
        ?NODErelease1 <http://data.rewire.it#linked> ?NODElabel;
                      dc:title ?release1Title;
                      mo:discogs ?release1Discogs;
                      rdf:type ?release1Type.
                      
        ?NODElabel <http://data.rewire.it#linked> ?NODErelease2;
                   foaf:name ?labelName;
                   mo:discogs ?labelDiscogs;
                   rdf:type ?labelType.
        
        ?NODEartist2 <http://data.rewire.it#linked> ?NODErelease2;
                     foaf:name ?artist2name;
                     mo:discogs ?artist2Discogs;
                     rdf:type ?artist2Type.
                     
        ?NODErelease2 dc:title ?release2Title;
                      mo:discogs ?release2Discogs;
                      rdf:type ?release2Type.
                      
      }
      WHERE{
        ?NODEartist1 mo:discogs INPUT:;
                foaf:name ?artist1Name;
                 mo:discogs ?artist1Discogs;
                 rdf:type ?artist1Type;
                 foaf:made ?NODErelease1.
        
        ?NODErelease1 dateIssued: "%(year)s"^^xsd:year;
                     dc:title ?release1Title;
                     rdf:type ?release1Type;
                     mo:discogs ?release1Discogs.
    
        # - - - - - - - - - - - - - - - - -
    
        ?NODErelease1 mo:publisher ?NODElabel.
    
        ?NODElabel foaf:name ?labelName;
               mo:discogs ?labelDiscogs;
               rdf:type ?labelType.
    
        # - - - - - - - - - - - - - - - - -
    
        ?NODErelease2 mo:publisher ?NODElabel.
        
        ?NODErelease2 dateIssued: "%(year)s"^^xsd:year;
                      dc:title ?release2Title;
                      mo:discogs ?release2Discogs;
                      rdf:type ?release2Type.
    
        # - - - - - - - - - - - - - - - - -
        
        ?NODErelease2 foaf:maker ?NODEartist2.
        
        ?NODEartist2 foaf:name ?artist2name;
                 mo:discogs ?artist2Discogs;
                 rdf:type ?artist2Type.
      }
      LIMIT 100
      """% {'url':url,'year':year}
    
    #discogsAPI.user_agent = 'discorrelate/0.1 +http://www.rewire.it'
    print q

    apiKey = '5dac588049e18e51fead5e788dc2449e38c2077a'
    
    results = getQuery(apiKey, "discogs", q)

    jsonny = flatten(results)
    
    return HttpResponse(jsonny, content_type="application/json; charset=utf8")

#    elif query == 'colabs':
#        q = """
#        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
#        PREFIX mo: <http://purl.org/ontology/mo/>
#        PREFIX dc: <http://purl.org/dc/terms/>
#        CONSTRUCT {
#          
#        }
#        SELECT DISTINCT ?artist ?name WHERE{
#        <""" + url + """> foaf:made ?release.
#        ?artist foaf:made ?release.
#        ?artist foaf:name ?name.
#        }
#        """
#        
#    elif query == 'comps':
#        q = """
#        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
#        PREFIX mo: <http://purl.org/ontology/mo/>
#        PREFIX dc: <http://purl.org/dc/terms/>
#        SELECT DISTINCT ?artist ?name WHERE{
#        <""" + url + """> foaf:made ?release.
#        ?artist foaf:made ?release.
#        ?artist foaf:name ?name.
#        }
#        """