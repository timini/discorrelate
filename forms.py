'''
Created on Oct 6, 2011

@author: tim
'''
from django import forms

query_choices = (
    ('labels', 'Linked by labels'),
    ('colabs', 'Collaborations'),
    ('comps', 'On compilations together')
)

class requestForm(forms.Form):
    url = forms.URLField(help_text="please enter a URI beginning http://data.kasabi.com/dataset/discogs/")
    year = forms.IntegerField(min_value=1000, max_value=2012)
    query = forms.ChoiceField(query_choices)