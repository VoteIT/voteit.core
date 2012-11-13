from urllib import urlencode

import httplib2
from colander import null
from colander import Invalid
from deform.widget import CheckedInputWidget
from deform.widget import RadioChoiceWidget
from deform.widget import TextAreaWidget
from pyramid.threadlocal import get_current_request
from webhelpers.html.tools import strip_links

from voteit.core.fanstaticlib import star_rating


class StarWidget(RadioChoiceWidget):
    """ Star widget for raiting alternatives.
        Use keyword creator_info to pass along creator information.
        See voteit.schulze.models for example code.
    """
    template = 'star_choice'
    readonly_template = 'readonly/star_choice'

    def __init__(self, **kw):
        super(StarWidget, self).__init__(**kw)
        star_rating.need()


class RecaptchaWidget(CheckedInputWidget):
    template = 'captcha'
    readonly_template = 'captcha'
    requirements = ()
    url = "www.google.com/recaptcha/api/verify"
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    testing = False
    
    def __init__(self, captcha_public_key = u'', captcha_private_key = u'', testing = False):
        super(RecaptchaWidget, self).__init__()
        self.captcha_public_key = captcha_public_key
        self.captcha_private_key = captcha_private_key
        self.testing = testing

    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (null, None):
            cstruct = '' #pragma : no cover
        confirm = getattr(field, 'confirm', '')
        template = readonly and self.readonly_template or self.template
        return field.renderer(template, field=field, cstruct=cstruct,
                              public_key=self.captcha_public_key,
                              )

    def deserialize(self, field, pstruct):
        #We can't test this part properly since it requires Google API connection :(
        if pstruct is null:
            return null
        challenge = pstruct.get('recaptcha_challenge_field') or ''
        response = pstruct.get('recaptcha_response_field') or ''
        if not response:
            raise Invalid(field.schema, 'No input')
        if not challenge:
            raise Invalid(field.schema, 'Missing challenge')
        request = get_current_request()
        url = "%s://%s" % (request.scheme, self.url)
        remoteip = request.remote_addr
        data = urlencode(dict(privatekey=self.captcha_private_key,
                              remoteip=remoteip,
                              challenge=challenge,
                              response=response))
        h = httplib2.Http(timeout=10)
        try:
            if self.testing:
                resp = {'status': '200'}
                content = "true\nno reason"
            else:
                resp, content = h.request(url,
                                          "POST",
                                          headers=self.headers,
                                          body=data)
        except AttributeError as e:
            if e == "'NoneType' object has no attribute 'makefile'":
                ## XXX: catch a possible httplib regression in 2.7 where
                ## XXX: there is no connection made to the socker so
                ## XXX sock is still None when makefile is called.
                raise Invalid(field.schema,
                              "Could not connect to the captcha service.")
        if not resp['status'] == '200':
            raise Invalid(field.schema,
                          "There was an error talking to the recaptcha \
                          server{0}".format(resp['status']))
        valid, reason = content.split('\n')
        if not valid == 'true':
            if reason == 'incorrect-captcha-sol':
                reason = "Incorrect solution"
            raise Invalid(field.schema, reason.replace('\\n', ' ').strip("'") )


class TextAreaStripLinksWidget(TextAreaWidget):
    ''' TextArea Widget that removes links '''
    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (null, None):
            cstruct = '' #pragma : no cover
        return super(TextAreaWidget, self).serialize(field, strip_links(cstruct), readonly)
