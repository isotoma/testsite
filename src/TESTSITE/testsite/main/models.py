import pysvn
import os

from django.db import models
from django.contrib import admin

from othermodels import Flavour, get_svn_client, get_svn_details
import testsite.settings as settings


class TestProject(models.Model):
    
    name = models.CharField(max_length = 200)
    svn_url = models.URLField(verify_exists=False)
    
    def __unicode__(self):
        return self.name
    
    @property
    def project_dir(self):
        project_dir = os.path.join(settings.TEST_BASE_DIR, self.name)
        return project_dir
    
    def needs_update(self):
        
        svn_client = get_svn_client()
        
        statuses = svn_client.status(self.project_dir, get_all = False, update = True)
        
        return len(statuses)
    
    def update_svn(self):
        
        # check that the checkout dir exists
        
        if not os.path.exists(self.project_dir):
            os.mkdir(self.project_dir)
        
        # get a checkout
        svn_client = get_svn_client()
        
        # work out if we need to update or checkout
        if os.path.exists(os.path.join(self.project_dir, '.svn')):
            svn_client.update(self.project_dir)
        else:
            svn_client.checkout(self.svn_url, self.project_dir)
            
    def get_test_flavours(self):
        
        files = os.listdir(self.project_dir)
        xml_files = [f[:-4] for f in files if f.endswith('.xml')]
        return xml_files
        
    def get_flavour(self, flavour):
        
        flavour = flavour + '.xml'
        files = os.listdir(self.project_dir)
        if not flavour in files:
            raise Exception("Flavour not found")
        
        f = Flavour(os.path.join(self.project_dir, flavour), self)
        
        return f
    
    def check_for_local_changes(self):
        
        svn_client = get_svn_client()
        statuses = svn_client.status(self.project_dir)
        
        for status in statuses:
            if status['text_status'] != pysvn.wc_status_kind.normal:
                return True
        return False
    
    def commit(self, message):
        
        svn_client = get_svn_client()
        svn_client.checkin(self.project_dir, message)
    
admin.site.register(TestProject)