# -*- coding: utf-8 -*-

from connection import Connection


class OTRXMPPChannel(object):
    """
    OTR-XMPP communications channel
    -------------------------------
    Uses Off-the-Record Messaging for communications with XMPP destinations
    See https://otr.cypherpunks.ca/

    Example::

    import time
    from otrxmppchannel import OTRXMPPChannel
    from otrxmppchannel.connection import OTR_TRUSTED, OTR_UNTRUSTED,
        OTR_UNENCRYPTED, OTR_UNKNOWN

    privkey = open('.otrprivkey', 'r').read()
    channel = OTRXMPPChannel(
        'bradass87@jabber.ccc.de/datadiode',
        'supersecret',
        [
            (
                'mendax@jabber.wikileaks.org',
                '33eb6b01c97ceba92bd6b5e3777189c43f8d6f03'
            ),
            'esnowden@chat.nsa.gov'
        ],
        privkey
    )

    def my_receive(msg, from_jid, otr_state):
        state = ''
        if otr_state == OTR_TRUSTED:
            state = 'trusted'
        elif otr_state == OTR_UNTRUSTED:
            state = 'UNTRUSTED!'
        elif otr_state == OTR_UNENCRYPTED:
            state = 'UNENCRYPTED!'
        else:
            state = 'UNKNOWN OTR STATUS!'
        print('received %s from %s (%s)' % (msg, from_jid, state))

    channel.send('')  # set up OTR
    time.sleep(3)
    channel.send('This message should be encrypted')

    NOTE: XMPP invitations are not handled
    NOTE: It seems to take roughly 3 seconds to set up an OTR session.
        Messages sent before the session is ready may be lost.

    :param jid: source JID, e.g. 'myapp@jabber.riseup.net'
    :param password: XMPP server password
    :param recipients: a single recipient JID, a tuple of
        *(jid, OTRFingerprint/None)*, or a list of same
    :param privkey: base64-encoded DSA private key for OTR. If *None* is
        passed, a new key will be generated and dumped via a *ValueError*
        exception.
    """

    def __init__(self, jid, password, recipients, privkey=None):
        usage = 'recipients can be a single recipient JID, a tuple of ' \
                '(jid, OTRFingerprint|None), or a list of same. Example: ' \
                '[\'untrustedrecipient@jabber.ccc.de\', ' \
                '(\'trustedrecipient@jabber.ccc.de\', ' \
                '\'43d36b01c67deba92bd6b5e3711189c43f8d6f04\')].'
        # normalize recipients to a list of tuples
        if isinstance(recipients, str):
            self.recipients = [(recipients, None)]
        elif isinstance(recipients, tuple):
            self.recipients = [recipients]
        elif isinstance(recipients, list):
            self.recipients = recipients
        else:
            raise TypeError(usage)
        for i in range(0, len(self.recipients) - 1):
            if isinstance(self.recipients[i], str):
                self.recipients[i] = self.recipients[i], None
            elif isinstance(self.recipients[i], tuple):
                if len(self.recipients[i]) > 2 or len(self.recipients[i]) < 1:
                    raise TypeError(usage)
                if len(self.recipients[i]) == 1:
                    self.recipients[i] = self.recipients[i], None
            else:
                raise TypeError(usage)
        self.connection = Connection(jid, password, privkey, self.on_receive)
        self.connection.start()

    def send(self, message):
        """
        Send *message* to recipients
        :param message: message string
        """
        for recipient in self.recipients:
            self.connection.send(message, recipient)

    def on_receive(self, message, from_jid, otr_state):
        """
        Override this method to create a custom message receipt handler. The
        handler provided simply discards received messages. Here is an
        example::

        from connection import OTR_TRUSTED, OTR_UNTRUSTED, OTR_UNENCRYPTED

        if otr_state == OTR_TRUSTED:
            state = 'trusted'
        elif otr_state == OTR_UNTRUSTED:
            state = 'UNTRUSTED!'
        elif otr_state == OTR_UNENCRYPTED:
            state = 'UNENCRYPTED!'
        else:
            state = 'UNKNOWN OTR STATUS!'
        print('received %s from %s (%s)' % (message, from_jid, state))

        :param message: received message body
        :param from_jid: source JID of the message
        :param otr_state: an integer describing the state of the OTR
            relationship to the source JID (OTR_* constants defined in
            otrxmppchannel.connection)
        """
        pass
