'''
Created on Jul 4, 2011

@author: tim
'''
import pytassium
import time

def SPARQLAndRespond(dataset, query):
    response, data = dataset.select(query)
    if response.status in range(200,300):
        # data now contains a dictionary of results
        import pprint
        #pprint.pprint(data)
        return data
    else:
        print "Oh no! %d %s " % (response.status, response.reason)
        
### API KEY ###

apiKey = '5dac588049e18e51fead5e788dc2449e38c2077a'

##==---------------------==## 
##-    Ordnance-Survey    -##
##==---------------------==##

OSdataset = pytassium.Dataset('ordnance-survey-linked-data',apiKey)

AllBouroughsWithGIS = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX admingeo: <http://data.ordnancesurvey.co.uk/ontology/admingeo/>
PREFIX geometry: <http://data.ordnancesurvey.co.uk/ontology/geometry/>

select * where {
?s rdf:type admingeo:Borough.
?s geometry:extent ?o
}
"""

#SPARQLAndRespond(OSdataset, AllBouroughsWithGIS)

##==---------------------==## 
##-       Education       -##
##==---------------------==##

EducationDataset = pytassium.Dataset('education',apiKey)

LatymerSchoolQuery = '''
SELECT * WHERE {
<http://education.data.gov.uk/id/school/102055> ?p ?o.
}
'''

#SPARQLAndRespond(EducationDataset, LatymerSchoolQuery)

##==---------------------==##
##-   Species in the UK   -##
##==---------------------==##

GeoSpecies = pytassium.Dataset('geospecies', apiKey)

SpeciesInUKWithCommonName = """
PREFIX geospecies: <http://rdf.geospecies.org/ont/geospecies#>
PREFIX uk:             <http://sws.geonames.org/2635167/>
SELECT * WHERE{
?species geospecies:hasCommonName ?name;
geospecies:isExpectedIn uk:.
}
"""

speciesTest = """
PREFIX geospecies:     <http://rdf.geospecies.org/ont/geospecies#>
PREFIX uk:             <http://sws.geonames.org/2635167/>
PREFIX bats:           <http://lod.geospecies.org/orders/TuTld>
PREFIX dcterms:        <http://purl.org/dc/terms/>

SELECT DISTINCT ?family_name ?canonicalName ?speciesconcept ?geospeciespage

WHERE {
?x geospecies:hasFamilyName ?family_name;
 geospecies:hasCanonicalName ?canonicalName;
 dcterms:identifier ?speciesconcept;
 geospecies:hasGeoSpeciesPage ?geospeciespage;
 geospecies:inOrder bats:;
 geospecies:isExpectedIn uk:.
}
ORDER BY ?family_name ?canonicalName
"""

#data = SPARQLAndRespond(GeoSpecies, SpeciesInUKWithCommonName)

#for result in data[1]:
#    print result['name']
    
##==---------------------==##
##-         DISCOGS       -##
##==---------------------==##

Discogs = pytassium.Dataset('discogs', apiKey)

artistsJoinedByLabels = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX mo: <http://purl.org/ontology/mo/>
SELECT DISTINCT ?artist2 ?name WHERE{
<http://data.kasabi.com/dataset/discogs/artist/cti> foaf:made ?release.
?release mo:publisher ?label.
?release2 mo:publisher ?label.
?artist2 foaf:made ?release2.
?artist2 foaf:name ?name.
}
"""

Colabs = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX dc: <http://purl.org/dc/terms/>

SELECT DISTINCT ?artist WHERE{
<http://data.kasabi.com/dataset/discogs/artist/cti> foaf:made ?release.
?artist foaf:made ?release.
}
"""

Compalations = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX dc: <http://purl.org/dc/terms/>

SELECT DISTINCT ?artist2 WHERE{
<http://data.kasabi.com/dataset/discogs/artist/jan-hammer> foaf:made ?release.
?release <http://xmlns.com/foaf/0.1/maker> ?artist2. 
}
"""
# <http://data.kasabi.com/dataset/discogs/artist/various>

#data = SPARQLAndRespond(Discogs, artistsJoinedByLabels)

##==-------------------------==##
##==     MUSICBRAINZ         ==##
##==-------------------------==##

mb = pytassium.Dataset('musicbrainz', apiKey)
bbcMu = pytassium.Dataset('bbc-music', apiKey)

findMembers = """
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?mb WHERE{
?group mo:discogs <http://www.discogs.com/artist/Radiohead>.
?group foaf:member ?member.
?member mo:musicbrainz ?mb.
}
"""
discogs2lastfm = """
PREFIX mo: <http://purl.org/ontology/mo/>
SELECT * where{
?artist mo:musicbrainz <%s>.
?artist mo:wikipedia ?wiki
}
"""
data = SPARQLAndRespond(mb, findMembers)

wikiPages = []
for result in data[1]:
    query = discogs2lastfm % result['mb'].decode()
    data2 = SPARQLAndRespond(bbcMu, query)
    for result in data2[1]:
        wikiPages.append(result['wiki'])
        
##==-------------------------==##
##==         DBPEDIA         ==##
##==-------------------------==##

dbpedia = pytassium.Dataset('dbpedia-36', apiKey)

artistDetails = '''
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
PREFIX dbpedia-prop: <http://dbpedia.org/property/>
select * where{
?s foaf:page <%s>.
?s dbpedia-prop:origin ?origin.
?s dbpedia-prop:dateOfBirth ?dob.
?s dbpedia-owl:instrument ?instrument.
?s dbpedia-owl:genre ?genre.
}
'''

for page in wikiPages:
    query = artistDetails % page
    data3 = SPARQLAndRespond(dbpedia, query)
    for result in data3[1]:
        print result