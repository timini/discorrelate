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
import discogs_client as discogsAPI
import pytassium

def SPARQLAndRespond(dataset, query):
    response, data = dataset.select(query)
    if response.status in range(200,300):
        # data now contains a dictionary of results
        #import pprint
        #pprint.pprint(data)
        return data
    else:
        print "Oh no! %d %s " % (response.status, response.reason)
        return False

def jsonTree(s, p, o):
    sent = dict()
    sent[s[0][0]] = s[1][0][s[0][0]].decode()
    objects = dict()
    for i, result in enumerate(o[1]):
        node = dict()
        for varName in result:
            node[varName] = result[varName].decode()
        objects['node'+str(i)] = node
    sent[p] = objects
    return simplejson.dumps(sent)

def jsonNodeLink(s,p,o):
    nodes = []
    links = []
    nodes.append({s[0][0] : s[1][0][s[0][0]].decode()})
    for i, result in enumerate(o[1]):
        node = dict()
        for varName in result:
            node[varName] = result[varName].decode()
        nodes.append(node)
        links.append({'source':0,'target':i+1,'value':10})
    return simplejson.dumps({'nodes':nodes, 'links':links})

def root(request):
    if not request.POST:
        form = requestForm()
        c = RequestContext(request, {'form':form})
        c.update(csrf(request))
        return render_to_response('root.html',c)
    url = request.POST.get('url')
    query = request.POST.get('query')
    
    if query == 'labels':
        q = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX mo: <http://purl.org/ontology/mo/>
        SELECT DISTINCT ?artist ?name WHERE{
        <""" + url + """> foaf:made ?release.
        ?release mo:publisher ?label.
        ?release2 mo:publisher ?label.
        ?artist foaf:made ?release2.
        ?artist foaf:name ?name.
        }
        """
        
    elif query == 'colabs':
        q = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX mo: <http://purl.org/ontology/mo/>
        PREFIX dc: <http://purl.org/dc/terms/>
        SELECT DISTINCT ?artist ?name WHERE{
        <""" + url + """> foaf:made ?release.
        ?artist foaf:made ?release.
        ?artist foaf:name ?name.
        }
        """
        
    elif query == 'comps':
        q = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX mo: <http://purl.org/ontology/mo/>
        PREFIX dc: <http://purl.org/dc/terms/>
        SELECT DISTINCT ?artist ?name WHERE{
        <""" + url + """> foaf:made ?release.
        ?artist foaf:made ?release.
        ?artist foaf:name ?name.
        }
        """
    
    discogsAPI.user_agent = 'discorrelate/0.1 +http://www.rewire.it'

    apiKey = '5dac588049e18e51fead5e788dc2449e38c2077a'
    Discogs = pytassium.Dataset('discogs', apiKey)
    
    rootQuery = """PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    Select ?name where{<""" + url + """> foaf:name ?name.
    }"""
    subject = SPARQLAndRespond(Discogs, rootQuery)
    results = SPARQLAndRespond(Discogs, q)
    
    jsonny = jsonNodeLink(subject, query, results)
    
    return HttpResponse(jsonny, content_type="application/json; charset=utf8")