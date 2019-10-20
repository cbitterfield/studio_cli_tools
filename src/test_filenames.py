#!/usr/bin/env python3

import os,sys,csv

filename = 'site_project.csv'

replace_from = 'EDGE01/DATAVOL4'
replace_to = '/edge'
records = 0
good = 0
bad = 0


input_file = csv.DictReader(open(filename))

for row in input_file:
    edge_id = row['edge_id']
    edge_path = row['path'].replace(replace_from,replace_to)
    
    
    if os.path.isfile(edge_path):
        print('Edge ID: {0} Path: {1} Good'.format(edge_id,edge_path))
        good = good + 1
    else:
        print('Edge ID: {0} Path: {1} Not Found'.format(edge_id,edge_path))
        bad = bad+ 1
    records = records + 1
    
print('{0} Records Processed, {1} Good, and {2} Bad'.format(records,good,bad))