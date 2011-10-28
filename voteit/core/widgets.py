from urllib import urlencode

import httplib2
from colander import null
from colander import Invalid
from deform.widget import CheckedInputWidget
from deform.widget import RadioChoiceWidget
from pyramid.threadlocal import get_current_request

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
    url = "http://www.google.com/recaptcha/api/verify"
    headers = {'Content-type': 'application/x-www-form-urlencoded'}

    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (null, None):
            cstruct = ''
        confirm = getattr(field, 'confirm', '')
        template = readonly and self.readonly_template or self.template
        request = get_current_request()
        captcha_public_key = request.registry.settings['captcha_public_key']
        return field.renderer(template, field=field, cstruct=cstruct,
                              public_key=captcha_public_key,
                              )

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        challenge = pstruct.get('recaptcha_challenge_field') or ''
        response = pstruct.get('recaptcha_response_field') or ''
        if not response:
            raise Invalid(field.schema, 'No input')
        if not challenge:
            raise Invalid(field.schema, 'Missing challenge')
        request = get_current_request()
        captcha_private_key = request.registry.settings['captcha_private_key']
        remoteip = request.remote_addr
        data = urlencode(dict(privatekey=captcha_private_key,
                              remoteip=remoteip,
                              challenge=challenge,
                              response=response))
        h = httplib2.Http(timeout=10)
        try:
            resp, content = h.request(self.url,
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
