# -*- coding: utf-8 -*-
#
# Thanks to Kjell (fnord) Braden for the Python OTR module and for his Gajim
# plugin implementation: https://github.com/afflux/potr/ and
# https://github.com/afflux/gotr/
#
# Thanks to Darrik L. Mazey (@darrikmazey) for documenting his implementation:
# https://blog.darmasoft.net/2013/06/30/using-pure-python-otr.html

from base64 import b64encode, b64decode

import xmpp
import potr
import potr.crypt
from potr.compatcrypto import generateDefaultKey


DEFAULT_POLICY_FLAGS = {
    'ALLOW_V1': False,
    'ALLOW_V2': True,
    'REQUIRE_ENCRYPTION': True,
    'SEND_TAG': True,
    'WHITESPACE_START_AKE': True,
    'ERROR_START_AKE': True,
}

PROTOCOL = 'xmpp'
MMS = 1024


# noinspection PyPep8Naming
class OTRContext(potr.context.Context):
    def __init__(self, account, client, peer, fp):
        super(OTRContext, self).__init__(account, peer)
        self.account = account
        self.client = client
        self.peer = peer
        self.fp = fp
        self.checkfp = False
        if fp is not None:
            self.fp = self.fp.lower()
            self.checkfp = True

    def getPolicy(self, key):
        if key in DEFAULT_POLICY_FLAGS:
            return DEFAULT_POLICY_FLAGS[key]
        return False

    def setState(self, newstate):
        theirfp = 'None'
        if self.crypto.theirPubkey.fingerprint() is not None:
            theirfp = self.crypto.theirPubkey.fingerprint().encode('hex')
        if newstate == potr.context.STATE_ENCRYPTED:
            if self.checkfp:
                if self.fp == theirfp:
                    self.setCurrentTrust('manual')
                else:
                    self.setCurrentTrust('untrusted')
            else:
                pass
        else:
            self.setCurrentTrust(None)
        super(OTRContext, self).setState(newstate)

    # noinspection PyUnusedLocal
    def inject(self, msg, appdata=None):
        self.client.send(
            xmpp.protocol.Message(to=self.peer, body=msg, typ='chat'))


# noinspection PyPep8Naming
class OTRAccount(potr.context.Account):
    def __init__(self, jid, pk=None):
        global PROTOCOL, MMS
        super(OTRAccount, self).__init__(jid, PROTOCOL, MMS)
        if pk is None:
            pkb64 = b64encode(generateDefaultKey().serializePrivateKey())
            msg = 'A base64-encoded DSA OTR private key for the XMPP' \
                  'account is required. Here is a fresh one you can use: \n'
            raise ValueError(msg + pkb64)
        else:
            self.pk = potr.crypt.PK.parsePrivateKey(b64decode(pk))[0]

    def loadPrivkey(self):
        return self.pk

    def savePrivkey(self):
        pass

    def saveTrusts(self):
        pass


class OTRManager(object):
    def __init__(self, account):
        self.account = account
        self.ctxs = {}

    def get_context(self, client, jid, fp=None):
        if jid in self.ctxs:
            return self.ctxs[jid]
        self.ctxs[jid] = OTRContext(self.account, client, jid, fp)
        return self.ctxs[jid]

    def destroy_context(self, jid):
        if jid in self.ctxs:
            del self.ctxs[jid]

    def destroy_all_contexts(self):
        for jid in self.ctxs.keys():
            self.destroy_context(jid)