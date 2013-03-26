#!/usr/bin/env python3

import sys

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

import datetime

if len(sys.argv) <= 1:
	print('Specify the version number as parameter')
	sys.exit()
version = sys.argv[1]

out_file = "atom.atom"
in_file = out_file

now = datetime.datetime.now()
now_iso = now.isoformat()

atom_url = "http://www.w3.org/2005/Atom"

#Some utilities functions
def atom_tag(tag):
	#Return a tag in the atom namespace
	return "{{{}}}{}".format(atom_url,tag)
	
def atom_SubElement(parent,tag):
	return ET.SubElement(parent,atom_tag(tag))
	
class YDLUpdateAtomEntry(object):
	def __init__(self,parent,title,id ,link, downloads_link):
		self.entry = entry = atom_SubElement(parent, "entry")
		#We set the values:
		atom_id = atom_SubElement(entry, "id")
		atom_id.text = id
		atom_title = atom_SubElement(entry, "title")
		atom_title.text = title
		atom_link = atom_SubElement(entry, "link")
		atom_link.set("href", link)
		atom_content = atom_SubElement(entry, "content")
		atom_content.set("type", "xhtml")
		#Here we go:
		div = ET.SubElement(atom_content,"div")
		div.set("xmlns", "http://www.w3.org/1999/xhtml")
		div.text = "Downloads available at "
		a = ET.SubElement(div, "a")
		a.set("href", downloads_link)
		a.text = downloads_link
		
		#Author info
		atom_author = atom_SubElement(entry, "author")
		author_name = atom_SubElement(atom_author, "name")
		author_name.text = "The youtube-dl maintainers"
		#If someone wants to put an email adress:
		#author_email = atom_SubElement(atom_author, "email")
		#author_email.text = the_email
		
		atom_updated = atom_SubElement(entry,"updated")
		up = parent.find(atom_tag("updated"))
		atom_updated.text = up.text = now_iso
	
	@classmethod
	def entry(cls,parent, version):
		update_id = "youtube-dl-{}".format(version)
		update_title = "New version {}".format(version)
		downloads_link = "http://youtube-dl.org/downloads/{}/".format(version)
		#There's probably no better link
		link = "http://rg3.github.com/youtube-dl"
		return cls(parent, update_title, update_id, link, downloads_link)
		

atom = ET.parse(in_file)

root = atom.getroot()

#Otherwise when saving all tags will be prefixed with a 'ns0:'
ET.register_namespace("atom",atom_url)

update_entry = YDLUpdateAtomEntry.entry(root, version)

#Find some way of pretty printing
atom.write(out_file,encoding="utf-8",xml_declaration=True)
