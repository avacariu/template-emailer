import smtplib
import ConfigParser
from db_manager import DBManager
import time
import threading

config = ConfigParser.RawConfigParser()
config.read('config.ini')
db_loc = config.get('app', 'database')
interval = int(config.get('app', 'interval'))
print interval
username = config.get('server', 'username')
password = config.get('server', 'password')

sender_name = config.get('app', 'name')

class MailThread(threading.Thread):
    def __init__(self, host, port, sender, *args, **kwargs):
        super(MailThread, self).__init__(*args, **kwargs)
        self.host = host
        self.port = port
        self.sender = sender
        self.server = smtplib.SMTP(host, port)
        self.server.ehlo()
        self.server.starttls()
        self.server.ehlo()
        self.server.login(username, password)

        self.finished = threading.Event()

    def send(self, dest, subject, body):
        message = """From: %s <%s>
To: <%s>
Subject: %s

%s
""" % (sender_name,self.sender, dest, subject, body)

        try:
            self.server.sendmail(self.sender, dest, message)
            print self.sender
            print dest
            print message
            return 0

        except smtplib.SMTPException:
            self.restart_server()
            self.send(dest, subject, body)

        except Exception, e:
            # TODO: better exception handling
            self.restart_server()
            self.send(dest, subject, body)

    def restart_server(self):
        self.server = smtplib.SMTP(self.host, self.port)
        self.server.ehlo()
        self.server.starttls()
        self.server.ehlo()
        self.server.login(username, password)

    def run(self):
        dbm = DBManager(db_loc)

        while not self.finished.is_set():
            self._run_helper(dbm)
            self.finished.wait(60.0 * interval)

        return

    def _run_helper(self, dbm):
        try:
            i = dbm.retrieve_next().next()
            self.send(i[1], i[2], i[3])

        except Exception, e:
            # if an exception arises, we need to ignore it and
            # try again for the next interval
            # self.send's exception is caught and dealt with within
            # that function
            pass

        else:
            dbm.delete(i[0])

    def stop(self):
        self.finished.set()
        self.join()
