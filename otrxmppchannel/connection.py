# -*- coding: utf-8 -*-

import xmpp
import threading
import time
from Queue import Queue
import potr
from otrmodule import OTRAccount, OTRManager

OTR_TRUSTED = 0
OTR_UNTRUSTED = 1
OTR_UNENCRYPTED = 2
OTR_UNKNOWN = 3


def d(msg):
    print('---> %s' % msg)


class AuthenticationError(Exception):
    pass


class OTRXMPPMessage(object):
    def __init__(self, body, to_jid, fp=None):
        self.body = body
        self.to_jid = to_jid
        self.fp = fp


class Connection(threading.Thread):
    def __init__(self, jid, password, pk, on_receive=None):
        threading.Thread.__init__(self)
        self.jid = xmpp.protocol.JID(jid)
        self.password = password
        self.on_receive = on_receive
        self.client = None
        self.q = Queue(maxsize=100)
        self.otr_account = OTRAccount(str(self.jid), pk)
        self.otr_manager = OTRManager(self.otr_account)

    def run(self):
        while True:
            while not self.client or not self.client.isConnected():
                cl = xmpp.Client(
                    self.jid.getDomain(),
                    debug=[]
                )
                conntype = cl.connect()
                if not conntype:
                    d('XMPP connect failed, retrying in 5 seconds')
                    time.sleep(5)
                    continue
                self.client = cl
            self.client.UnregisterDisconnectHandler(
                self.client.DisconnectHandler)
            auth = self.client.auth(self.jid.getNode(), self.password,
                                    self.jid.getResource())
            if not auth:
                d('XMPP authentication failed')
                raise AuthenticationError
            self.client.sendInitPresence(requestRoster=0)
            self.client.RegisterDisconnectHandler(self._on_disconnect)
            self.client.RegisterHandler('message', self._on_receive)
            while self.client.isConnected() and self.client.Process(0.1):
                if not self.q.empty():
                    self._send(self.q.get())
                pass

    def _on_disconnect(self):
        self.otr_manager.destroy_all_contexts()

    def _on_receive(self, _, stanza):
        fromjid = stanza.getFrom()
        body = str(stanza.getBody())
        # d('stanza from %s: %s' % (fromjid, body))
        if stanza.getBody() is None:
            return
        fromjid = xmpp.protocol.JID(fromjid)
        fromjid.setResource(None)
        otrctx = self.otr_manager.get_context(self.client, str(fromjid))
        encrypted = True
        res = ()
        try:
            res = otrctx.receiveMessage(body)
        except potr.context.UnencryptedMessage:
            encrypted = False
        except potr.context.NotEncryptedError:
            # potr auto-responds saying we didn't expect an encrypted message
            return

        msg = ''
        otr_state = OTR_UNKNOWN
        if not encrypted:
            if stanza['type'] in ('chat', 'normal'):
                msg = stanza.getBody()
                otr_state = OTR_UNENCRYPTED
                d('unencrypted message: %s' % msg)
        else:
            if res[0] is not None:
                msg = res[0]
                trust = otrctx.getCurrentTrust()
                if trust is None or trust == 'untrusted':
                    otr_state = OTR_UNTRUSTED
                    d('untrusted decrypted message: %s' % msg)
                else:
                    otr_state = OTR_TRUSTED
                    d('trusted decrypted message: %s' % msg)
        if msg is not None and msg != '':
            self.on_receive(msg, str(fromjid), otr_state)

    def _send(self, msg):
        # d('_send(%s, %s, %s)' % (msg.body, msg.to_jid, msg.fp))
        otrctx = self.otr_manager.get_context(self.client, msg.to_jid, msg.fp)
        if otrctx.state == potr.context.STATE_ENCRYPTED:
            if otrctx.getCurrentTrust() == 'untrusted':
                d('fingerprint changed from %s to %s for %s!' % (
                    msg.fp, otrctx.fp, msg.to_jid))
                self.client.send(
                    xmpp.protocol.Message(
                        msg.to_jid,
                        'I would like to tell you something, but I '
                        'don\'t trust your OTR fingerprint.'))
            else:
                otrctx.sendMessage(0, str(msg.body))
        else:
            # d('Initializing OTR with %s (message "%s")' % (
            #     msg.to_jid, msg.body))
            self.client.send(
                xmpp.protocol.Message(
                    msg.to_jid,
                    otrctx.account.getDefaultQueryMessage(otrctx.getPolicy),
                    typ='chat'))

    def send(self, text, to_jid, fp=None):
        """
        send a message to a JID, with an optional OTR fingerprint to verify
        :param text: message body
        :param to_jid: destination JID
        :param fp: expected OTR fingerprint from the destination JID
        :return:
        """
        while self.q.full():
            d('queue full, discarding first entry')
            _ = self.q.get_nowait()
        if isinstance(to_jid, tuple):
            to_jid, fp = to_jid
        self.q.put_nowait(OTRXMPPMessage(text, to_jid, fp))
