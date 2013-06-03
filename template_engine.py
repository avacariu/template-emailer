# Component that parses template and returns list of blocks
#  and allows you to put data into each block

import re

class TemplateEngine(object):
    def __init__(self, template):
        self.template = template
        self.__parse_for_blocks()

    def __parse_for_blocks(self):
        self.blocks = set(re.findall("\\{%\s*(.*?)\s*%\\}", self.template))

    def replace(self, **kwargs):
        if len(kwargs) == 0:
            return -1
        for key in kwargs:
            if key not in self.blocks:
                return -2
        
        # modified_txt not in init because we need text to be updated
        # as we go along. Each replacement needs to modify template
        # not the modified txt
        modified_txt = self.template[:]

        for k, v in kwargs.iteritems():
            modified_txt = re.sub("\\{%%\s+(%s)\s+%%\\}" % (k), v, modified_txt)

        return modified_txt





