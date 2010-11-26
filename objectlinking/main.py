from trac.core import Component, implements
from trac.web.api import IRequestHandler, ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider
import re
import pkg_resources
from trac.ticket.api import ITicketChangeListener
from trac.web.api import    RequestDone
from trac.web.chrome import  Chrome, add_stylesheet, add_javascript
from genshi.filters import Transformer
from genshi.builder import tag
import json
import trac
from pprint import pprint
from trac.web.href import Href
from trac.util.datefmt import parse_date
import re


__author__ = 'kosyakov'

def get_link_types():
    link_types={
                'relates':{'forth_label':"relates to", 'back_label':"relates to"},
                'parent':{'forth_label':"is subtask of", 'back_label':"has subtask"},
                'duplicate' :{'forth_label':"is duplicate of", 'back_label':"has duplicate in"},
                }
    return link_types


class LinkManipulator(object):
    def __init__(self, env):
        self.env = env
        self.ticket_RE = re.compile(r'#(\d+)', re.U)

    def parse_object_reference(self, req_args_source_):
        print "Parsing ", req_args_source_
        match = self.ticket_RE.match(req_args_source_)
        if match:
            type = 'ticket'
            id = match.groups()[0]
        else:
            data = [x.strip() for x in req_args_source_.split(':')]
            type, id = (data[0], data[1])
        return type, id

    def __call__(self, req):
        source_type, source_id = self.parse_object_reference(req.args['source'])
        target_type, target_id = self.parse_object_reference(req.args['target'])
        comment = req.args.get('comment',"")
        type = req.args['type']
        self.do_the_work(source_type, source_id, target_type, target_id, type, comment)
        req.redirect(req.args['return_url'])
        return ()

    def do_the_work(self, source_type, source_id, target_type, target_id, type, comment):
        pass

class CreateLinkController(LinkManipulator):

    def do_the_work(self, source_type, source_id, target_type, target_id, type, comment):
        db = self.env.get_read_db()
        cursor = db.cursor()
        INSERT_LINK_SQL = "INSERT INTO objectlink(source_type, source_id, target_type, target_id, link_type, comment) VALUES (%s,%s,%s,%s,%s, %s)"
        cursor.execute(INSERT_LINK_SQL, (source_type, source_id, target_type, target_id, type, comment))
        db.commit()

class DeleteLinkController(LinkManipulator):

    def do_the_work(self, source_type, source_id, target_type, target_id, type, comment):
        db = self.env.get_read_db()
        cursor = db.cursor()
        INSERT_LINK_SQL = "DELETE FROM objectlink WHERE source_type = %s AND source_id = %s AND target_type = %s AND target_id = %s AND link_type = %s"
        cursor.execute(INSERT_LINK_SQL, (source_type, source_id, target_type, target_id, type))
        db.commit()

class TicketLinksTransformer(object):

    def __init__(self, env):
        self.env = env

    def get_stream(self,req, method, filename, stream, original_data):
        chrome = Chrome(self.env)
        ticket_id = original_data['ticket'].id
        data = original_data
        data['objectlinks'] = self.get_links_for('ticket', ticket_id)
        data['link_types'] = get_link_types()
        data['components'] = [component.name for component in trac.ticket.model.Component.select(self.env)]
        data['return_url'] = req.href.ticket(ticket_id)
        template = chrome.load_template('ticket-links.html')
        content_stream = template.generate(**(chrome.populate_data(req, data)))
        add_javascript(req,'objectlinking/jquery-ui-autocomplete.js')
        add_javascript(req,'objectlinking/search-links.js')
        add_stylesheet(req, 'objectlinking/style.css')
        add_stylesheet(req, 'objectlinking/jquery-ui-custom.css')
        return Transformer('//div[@id="ticket"]').after(content_stream)

    def read_link_data_from_database(self, sql_statement, object_id, object_type):
        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute(sql_statement, (object_type, object_id))
        links = []
        for row in cursor:
            link_data = {'source_type': row[0], 'source_id': row[1], 'target_type': row[2], 'target_id': row[3], 'type': row[4], 'comment':row[5]}
            links.append(link_data)
        return links

    def get_links_for(self, object_type, object_id):
        FORTH_LINKS_SQL = "SELECT * FROM objectlink WHERE source_type = %s AND  source_id = %s"
        BACK_LINKS_SQL = "SELECT * FROM objectlink WHERE target_type = %s AND target_id = %s"
        back_links = self.read_link_data_from_database(BACK_LINKS_SQL, object_id, object_type)
        forth_links = self.read_link_data_from_database(FORTH_LINKS_SQL, object_id, object_type)
        self._add_object_titles(back_links)
        self._add_object_titles(forth_links)
        links = {
                'back_links':back_links,
                'forth_links':forth_links,
                }
        return links

    def _add_object_titles(self, links):
        data = {}
        for link in links:
            if link['source_type'] not in data: data[link['source_type']] = []
            data[link['source_type']].append(link['source_id'])
            if link['target_type'] not in data: data[link['target_type']] = []
            data[link['target_type']].append(link['target_id'])
        for type_name in data:
            if type_name == 'ticket':
                ticket_titles = self._get_ticket_titles(data[type_name])
                for link in links:
                    source_id = int(link['source_id'])
                    target_id = int(link['target_id'])
                    if source_id in ticket_titles:
                        link['source_title'] = ticket_titles[source_id]
                    if target_id in ticket_titles:
                        link['target_title'] = ticket_titles[target_id]
        for link in links:
            if 'source_title' not in link: link['source_title'] = None
            if 'target_title' not in link: link['target_title'] = None


    def _get_ticket_titles(self, ticket_ids):
        sql_statement = "SELECT id, summary FROM ticket WHERE id IN (%s)" % ','.join(ticket_ids)
        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute(sql_statement, ())
        titles = {}
        for row in cursor:
            titles[row[0]] = row[1]
        return titles


class SearchObjectsController(object):
    def __init__(self, env):
        self.env = env

    def __call__(self, req):
        string = req.args['q']
        db = self.env.get_read_db()
        cursor = db.cursor()
        SEARCH_TICKETS = "SELECT id, summary FROM ticket WHERE summary LIKE %s LIMIT 20"
        cursor.execute(SEARCH_TICKETS , ('%' + string + '%',))
        search_results = []
        for row in cursor:
            search_results.append({'type':'ticket','id':row[0],'title':row[1]})
        json_data = json.dumps(search_results)
        req.send_response(200)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(json_data))
        req.end_headers()
        req.write(json_data)
        raise RequestDone

#        return 'search-links-json.txt', data, 'application/json'


class AddTicketLinkInfoToFormTransformer(object):
    def __init__(self, env):
        self.env = env

    def get_stream(self,req, method, filename, stream, original_data):
        if 'linkinfo' in req.args:
            link_info = tag.input(name="linkinfo", value=req.args['linkinfo'], type="hidden")
        else:
            link_info = tag.comment('no link')
        return Transformer('//form[@id="propertyform"]').prepend(link_info)


class ObjectLinking(Component):

    implements(ITemplateStreamFilter, IRequestHandler, ITemplateProvider, ITicketChangeListener, IRequestFilter)

    def pre_process_request(self, req, handler):
        if re.match(r'/newticket', req.path_info) and 'linkinfo' in req.args:
            self.link_info = req.args['linkinfo']
        else:
            self.link_info = None
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

#   ITicketChangeListener

    def ticket_created(self,ticket):
        self.add_link_to_ticket(ticket)

    def ticket_changed(self,ticket, comment, author, old_values):
        pass

    def ticket_deleted(self,ticket):
        pass

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/link', req.path_info)

    def process_request(self, req):
        path_info = req.path_info.split('/')[2]
        controller = self.get_controller(path_info)
        return controller(req)

     # ITemplateProvider methods

    def get_htdocs_dirs(self):
       return [('objectlinking', pkg_resources.resource_filename('objectlinking', 'htdocs'))]

    def get_templates_dirs(self):
       return [pkg_resources.resource_filename('objectlinking', 'templates')]

    def filter_stream(self, req, method, filename, stream, original_data):
        transformer = self.get_transformer_for(req, method, filename)
        if transformer is None:
            return stream
        return stream | transformer.get_stream(req,method,filename,stream,original_data)

    def get_controller(self, path_info):
        controller = None
        if path_info == 'create':
            controller = CreateLinkController(self.env)
        if path_info == 'delete':
            controller = DeleteLinkController(self.env)
        if path_info == 'search':
            controller = SearchObjectsController(self.env)
        return controller

    def get_transformer_for(self, req, method, template_name):
        filter = None
        if re.match(r'/ticket', req.path_info) and template_name == 'ticket.html':
            filter = TicketLinksTransformer(self.env)
        if re.match(r'/newticket', req.path_info) and template_name == 'ticket.html':
            filter = AddTicketLinkInfoToFormTransformer(self.env)

        return filter

    def add_link_to_ticket(self, ticket):
        if self.link_info:
            target_type, target_id, type = [x.strip() for x in self.link_info.split(":")]
            add_link = CreateLinkController(self.env)
            add_link.do_the_work('ticket',ticket.id,target_type, target_id,type, None)
            self.link_info = None


