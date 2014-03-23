XMPP-OTR channel for Python
===========================

This is a Python library for communicating with XMPP destinations using
OTR (`Off-the-Record Messaging`_) encryption.

Features
--------

-  Your internet application can talk securely to you on your PC or
   smartphone using readily-available chat software with OTR support
-  OTRv2
-  Send to and receive from multiple destinations, with or without
   fingerprint verification
-  Pure python (no libotr dependency)

Example
-------

::

    import time
    from otrxmppchannel import OTRXMPPChannel
    from otrxmppchannel.connection import OTR_TRUSTED, OTR_UNTRUSTED,
        OTR_UNENCRYPTED, OTR_UNKNOWN

    # Load the base64-encoded OTR DSA key. Constructing the object without
    # a key will generate one and provide it via ValueError exception.
    privkey = open('.otrprivkey', 'r').read()

    class MyOTRChannel(OTRXMPPChannel):
        def on_receive(self, message, from_jid, otr_state):
            if otr_state == OTR_TRUSTED:
                state = 'trusted'
            elif otr_state == OTR_UNTRUSTED:
                state = 'UNTRUSTED!'
            elif otr_state == OTR_UNENCRYPTED:
                state = 'UNENCRYPTED!'
            else:
                state = 'UNKNOWN OTR STATUS!'
            print('received %s from %s (%s)' % (message, from_jid, state))

    mychan = MyOTRXMPPChannel(
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

    mychan.send('')  # Force OTR setup
    time.sleep(3)  # Wait a bit for OTR setup to complete
    mychan.send('This message should be encrypted')

Notes
-----

-  XMPP invitations are not handled
-  It seems to take roughly 3 seconds to set up an OTR session. Messages
   sent before the session is ready may be lost.
-  The private key serialization format is specific to pure-python-otr.
   Conversions from other formats are not handled.

Dependencies
------------

-  `xmpppy`_ (>= 0.4.1)
-  `pure-python-otr`_ (>= 1.0.0)

Author
------

-  `Mike Gogulski`_ - https://github.com/mikegogulski

Donations
---------

If you found this software useful and would like to encourage its
maintenance and further development, please consider making a donation
to the Bitcoin address ``1MWFhwdFVEhB3X4eVsm9WxwvAhaxQqNbJh``.

License
-------

This is free and unencumbered public domain software. For more
information, see http://unlicense.org/ or the accompanying UNLICENSE
file.

.. _Off-the-Record Messaging: https://otr.cypherpunks.ca/
.. _xmpppy: http://xmpppy.sourceforge.net/
.. _pure-python-otr: https://github.com/afflux/pure-python-otr
.. _Mike Gogulski: mailto:mike@gogulski.com