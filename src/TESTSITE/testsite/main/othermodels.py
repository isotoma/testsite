from lxml import etree
import os
from csv import writer
import tempfile
import codecs

import pysvn

from django.template.loader import get_template
from django.template import Context

def get_svn_client():
    svn_client = pysvn.Client()
    svn_client.callback_get_login = get_svn_details
    return svn_client

def get_svn_details(realm, username, may_save):
    return True, settings.svnuser, settings.svnpass, False

def get_xml_doc(path):
    """ Open the xml file from disk and return it as an etree """
    xml_file = codecs.open(path, encoding='utf-8').read()
    xml_doc = etree.fromstring(xml_file)
    return xml_doc

def _get_value(element, value):
    if element.find(value) is not None and element.find(value).text:
        return element.find(value).text
    return ""


class Flavour(object):

    def __init__(self, path, project):
        self.path = path
        self.name = self.path.split('/')[-1][:-4]
        self.project = project

    def __unicode__(self):
        return self.name
        
    @property
    def mbox(self):
        xml_doc = get_xml_doc(self.path)
        mbots = xml_doc.xpath('//mbot')
        
        final_mbots = []
        for mbot in mbots:
            box = mbox(mbot.attrib['name'], self)
            final_mbots.append(box)
            
        return final_mbots
    
    def get_specific_mbox(self, mbox_name):
        return mbox(mbox_name, self)
    
    def make_csv(self):
        
        f = tempfile.TemporaryFile()
        output = writer(f, delimiter = ',')
        output.writerow(['Test ID', 'Story ID', 'Summary', 'Steps', 'Expected Results', 'Priority', 'Actual Result', 'Pass / Fail'])
        
        for box in self.mbox:
            output.writerow([box.name, '', '', '', '', '', ''])
            
            for test in box.tests:
                data = []
                data.append(test.name)
                data.append(test.story_id)
                data.append(test.summary.encode('utf-8'))
                steps = test.steps
                new_steps = []
                for line in steps.split('\n'):
                    new_steps.append(line.strip())
                steps = '\n'.join(new_steps)
                data.append(steps.encode('utf-8'))
                data.append(test.expected_result.encode('utf-8'))
    
                data.append(test.priority)
        
                data.append(test.automated_test_id)
    
                #added for padding
                data.append('')
                data.append('')
                
                output.writerow(data)
        f.seek(0)
        
        filename = self.name + '.csv'
        
        return f, filename
        
    
class mbox(object):
    
    def __init__(self, name, flavour):
        self.name = name
        self.flavour = flavour
        
    def __unicode__(self):
        return self.friendly_name
    
    @property
    def friendly_name(self):
        doc = get_xml_doc(os.path.join(self.path, self.name +'.xml'))
        name = doc.xpath('//friendly_name')
        return name[0].text
    
    @property
    def path(self):
        return os.path.join(self.flavour.project.project_dir, self.name)
    
    @property
    def tests(self):
        test_list = [XMLTest(x[:-4], self) for x in os.listdir(self.path) if x.endswith('.xml') and x != self.name + '.xml']
        return test_list
    
    def get_specific_test(self, test_name):
        
        return XMLTest(test_name, self)
    
    
    
class XMLTest(object):
    
    def __init__(self, name, mbox, new = False):
        self.name = name.strip()
        self.mbox = mbox
        
        if not new:
            xml_doc = get_xml_doc(self.path)
            xpath = xml_doc.xpath('//test')[0]
            self.story_id = _get_value(xpath, 'story_id')
            self.summary = _get_value(xpath, 'summary')
            self.steps = _get_value(xpath, 'steps')
            self.expected_result = _get_value(xpath, 'expected_result')
            self.priority = _get_value(xpath, 'priority')
            self.automated_test_id = _get_value(xpath, 'automated_test_id')
        
    @property
    def path(self):
        return os.path.join(self.mbox.path, self.name + '.xml')
        
    def __unicode__(self):
        doc = get_xml_doc(self.path)
        names = doc.xpath('//name')
        return names[0].text
    
    def save(self):
        t = get_template('files/test.xml')
        xml = t.render(Context(self.__dict__))
        
        f = open(self.path, 'w')
        f.write(xml)
        f.flush()
        f.close()
        
        self.check_for_svn_addition()
        
    def check_for_svn_addition(self):
        svn_client = get_svn_client()
        info = svn_client.status(self.path)[0]
        if info['text_status'] == pysvn.wc_status_kind.unversioned:
            svn_client.add(self.path)
            
    def delete(self):
        
        svn_client = get_svn_client()
        svn_client.remove(self.path, force = True)
        

    