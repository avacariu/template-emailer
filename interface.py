import gtk
from template_engine import TemplateEngine
from db_manager import DBManager
import time

import threading

from mail_thread import MailThread

import ConfigParser as CP

config = CP.RawConfigParser()
config.read('config.ini')

db_loc = config.get('app', 'database')

host = config.get('server', 'smtp')
port = config.get('server', 'port')
sender = config.get('server', 'sender')
default_template = config.get('app', 'template')

gtk.gdk.threads_init()

class PreviewWindow(gtk.Window):
    def __init__(self, text):
        super(PreviewWindow, self).__init__()

        self.set_title("Preview")

        self.label = gtk.Label(text)
        self.label.set_line_wrap(True)

        self.add(self.label)
        self.show_all()

class CustomTextView(gtk.TextView):
    def __init__(self, name, *args, **kwargs):
        super(CustomTextView, self).__init__(*args, **kwargs)
        self.__name__ = name

class CreateInterface(gtk.Window):
    def __init__(self):
        super(CreateInterface, self).__init__()
        self.set_title("Create new email")

        self.vbox = gtk.VBox(True, 2)


        self.hbox = gtk.HBox(False, 2)
        self.template_label = gtk.Label("Template: ")
        self.template_entry = gtk.Entry()
        self.template_entry.set_text(default_template)
        self.template_select = gtk.Button("Select")
        self.template_select.connect("clicked", self._on_template_clicked)
        

        self.hbox.pack_start(self.template_label, expand = False)
        self.hbox.pack_start(self.template_entry)
        self.hbox.pack_start(self.template_select, expand = False)

        self.vbox.pack_start(self.hbox, expand=False)

        self.hbox_email = gtk.HBox(False,2)
        self.email_label = gtk.Label("Email: ")
        self.email = gtk.Entry()
        self.hbox_email.pack_start(self.email_label, expand=False)
        self.hbox_email.pack_start(self.email)

        
        self.hbox_subject = gtk.HBox(False,2)
        self.subject_label = gtk.Label("Subject: ")
        self.subject = gtk.Entry()
        self.hbox_subject.pack_start(self.subject_label, expand=False)
        self.hbox_subject.pack_start(self.subject)
        
        self.vbox.pack_start(self.hbox_email)
        self.vbox.pack_start(self.hbox_subject)

        self.txtbox_list = []

        self.add(self.vbox)
        self.show_all()

    def _on_template_clicked(self, arg):
        try:
            with open(".\\templates\\" + self.template_entry.get_text(), 'r') as f:
                template = f.read()
        except:
            md = gtk.MessageDialog(self, 
                    gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_CLOSE, "Unable to find specified template.")
            md.run()
            md.destroy()

        else:
            self.te = TemplateEngine(template)
            for block in self.te.blocks:
                exec """self.block_%s_label = gtk.Label('%s')
self.txtbox_%s = CustomTextView('%s')
self.vbox.pack_start(self.block_%s_label, expand=False)
self.vbox.pack_start(self.txtbox_%s, expand=True)
self.txtbox_list.append(self.txtbox_%s)""" % (block, block, block, block, block, block, block) in globals(), locals()


            self.preview_btn = gtk.Button("Preview")
            self.submit_btn = gtk.Button("Submit email")

            self.preview_btn.connect("clicked", self._on_preview_clicked)
            self.submit_btn.connect("clicked", self._on_submit_clicked)
            
            self.vbox.pack_start(self.preview_btn, expand=False)
            self.vbox.pack_start(self.submit_btn, expand=False)

            self.show_all()

    def _on_preview_clicked(self, arg):
        attr = {}

        for box in self.txtbox_list:

            buff = box.get_buffer()
            start = buff.get_start_iter()
            end = buff.get_end_iter()

            attr[box.__name__] = buff.get_text(start, end)


        text = self.te.replace(**attr)

        pw = PreviewWindow(text)
        self.show_all()
        
    def _on_submit_clicked(self, arg):
        attr = {}

        for box in self.txtbox_list:

            buff = box.get_buffer()
            start = buff.get_start_iter()
            end = buff.get_end_iter()

            attr[box.__name__] = buff.get_text(start, end)


        text = self.te.replace(**attr)
        dbm = DBManager(db_loc)
        dbm.insert(self.email.get_text(), self.subject.get_text(), text, 
                int(time.time()), self.template_entry.get_text())

        self.destroy()

class MainInterface(gtk.Window):
    def __init__(self):
        super(MainInterface, self).__init__()

        self.m = None # mailer

        self.set_title("Template Emailer")
        self.set_size_request(500, 500)
        
        self.set_position(gtk.WIN_POS_CENTER)

        self.vbox = gtk.VBox(False, 2)

        self.label = gtk.Label("From: %s" % (sender) )

        self.refresh = gtk.Button("Refresh")
        self.refresh.connect("clicked", self._on_refresh_clicked)

        self.liststore = gtk.ListStore(str, str, str, int)  # int is the id not shown
        self.tv = gtk.TreeView(self.liststore)

        self.tvcolumn = gtk.TreeViewColumn('Email', gtk.CellRendererText(), text=0)
        self.tvcolumn1 = gtk.TreeViewColumn('Subject', gtk.CellRendererText(), text=1)
        self.tvcolumn2 = gtk.TreeViewColumn('Time', gtk.CellRendererText(), text=2)

        self.tv.append_column(self.tvcolumn)
        self.tv.append_column(self.tvcolumn1)
        self.tv.append_column(self.tvcolumn2)

        self.tv.connect("key-release-event", self._on_key_release)

        self.create = gtk.Button("Create new email")
        self.create.connect("clicked", self._on_create_clicked)

        self.startmail = gtk.ToggleButton("Start automatic mailer")
        self.startmail.connect("toggled", self._on_startmail_toggled)

        self.vbox.pack_start(self.label, expand=False)
        self.vbox.pack_start(self.refresh, expand=False)
        self.vbox.pack_start(self.tv, expand=True)
        self.vbox.pack_start(self.create, expand=False)
        self.vbox.pack_start(self.startmail, expand=False)

        self.add(self.vbox)
        self.connect("destroy", self._quit)
        self.show_all()

    def _quit(self, *args):
        try:
            self.m.stop()
        except AttributeError:
            pass

        try:
            del self.m
        except Exception:
            pass

        gtk.main_quit(*args)

    def _on_create_clicked(self, arg):
        self.ci = CreateInterface()


    def _on_refresh_clicked(self,arg):
        dbm = DBManager(db_loc)

        self.liststore.clear()

        for i in dbm.retrieve_all():
            self.liststore.append([i[1], i[2], repr(i[4]), i[0]])

        self.show_all()

    def _on_startmail_toggled(self, arg):
        if self.m is None:
            self.m = MailThread(host, port, sender)
            self.m.setDaemon(True)


        if arg.get_active():
            if not self.m.is_alive():
                self.m = MailThread(host, port, sender) # cannot start a thread twice
                self.m.setDaemon(True)
                self.m.start()
        else:
            if self.m.is_alive():
                # set run_thread to false, and on next iteration of loop
                # it'll stop
                self.m.stop()

    def _on_key_release(self, widget, event):
        if event.keyval == 65535: # delete key
            sel = widget.get_selection().get_selected()
            item_id = self.liststore.get(sel[1], 3)[0]
            dbm = DBManager(db_loc)
            dbm.delete(item_id)
            self.liststore.remove(sel[1])
