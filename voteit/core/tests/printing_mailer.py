from pyramid_mailer.interfaces import IMailer


class PrintingMailer(object):
    """
    Dummy mailing instance. Simply prints all messages directly instead of handling them.
    Good for avoiding mailing users when you want to test things locally.
    """

    def send(self, message):    
        """
        Send, but really print content of message
        """
        
        print "Subject: %s" % message.subject
        print "To: %s" % ", ".join(message.recipients)
        print "======================================"
        print message.html
        print message.body

    send_to_queue = send_immediately = send


def includeme(config):
    print "\nWARNING! Using printing mailer - no mail will be sent!\n"
    mailer = PrintingMailer()
    config.registry.registerUtility(mailer, IMailer)
