#!/usr/bin/env python3
import sys
import json

target_version = sys.argv[1]

def empty_doc():
    return  [{"unMeta":{}}, []]

doc = json.loads(input())
body = doc[1]

    
# We get the text for each version
versions = {}
current_version = None
for el in body:
    el.keys()
    type_ = list(el.keys())[0]
    if type_ == 'Header':
        current_version = el['Header'][2][0]['Str']
        versions[current_version] = empty_doc()
    elif current_version is not None:
        versions[current_version][1].append(el)

# We get the document for the target version and create the json string for pandoc
version_changelog = versions.get(target_version, empty_doc())
print(json.dumps(version_changelog))

