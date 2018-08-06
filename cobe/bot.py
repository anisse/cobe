# Copyright (C) 2014 Peter Teichman

import irc.bot
import logging
import re
import functools
import jaraco.stream.buffer

log = logging.getLogger("cobe.bot")


class Bot(irc.bot.SingleServerIRCBot):
    def __init__(self, brain, servers, nick, channel, log_channel, ignored_nicks,
                 only_nicks):
        irc.bot.SingleServerIRCBot.__init__(self, servers, nickname=nick, realname=nick)

        # Fall back to latin-1 if invalid utf-8 is provided.
        irc.client.ServerConnection.buffer_class = jaraco.stream.buffer.LenientDecodingLineBuffer

        self.brain = brain
        self.nick = nick
        self.channel = channel
        self.log_channel = log_channel
        self.ignored_nicks = ignored_nicks
        self.only_nicks = only_nicks
        self.keepalive_running = False

        if log_channel is not None:
            # set up a new logger
            handler = IrcLogHandler(self.connection, log_channel)
            handler.setLevel(logging.DEBUG)

            logging.root.addHandler(handler)

    def _dispatcher(self, c, e):
        log.debug("on_%s %s", e.type, (e.source, e.target, e.arguments))
        irc.client.SimpleIRCClient._dispatcher(self, c, e)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def keep_alive(self):
        try:
            if self.connection.connected:
                self.connection.ping('keep-alive')
        except BaseException as e:
            # The keep-alive might be racy with a disconnection, and we don't
            # need it to bring down the program
            log.error("Exception while sending keepalive: %s", e)
            pass

    def on_welcome(self, conn, event):
        self.connection.join(self.channel)
        if not self.keepalive_running:
            keeper = functools.partial(self.keep_alive)
            self.connection.reactor.scheduler.execute_every(period=30, func=keeper)
            self.keepalive_running = True

        if self.log_channel:
            self.connection.join(self.log_channel)

    def on_pubmsg(self, conn, event):
        user = irc.client.NickMask(event.source).nick

        if event.target == self.log_channel:
            # ignore input in the log channel
            return

        # ignore specified nicks
        if self.ignored_nicks and user in self.ignored_nicks:
            return

        # only respond on channels
        if not irc.client.is_channel(event.target):
            return

        msg = event.arguments[0].strip()

        # strip pasted nicks from messages
        msg = re.sub("<\S+>\s+", "", msg)

        # strip kibot style quotes from messages
        match = re.match("\"(.*)\" --\S+, \d+-\S+\d+.", msg)
        if match:
            msg = match.group(1)

        # look for messages directed to a user
        match = re.match("\s*(\S+)[,:]\s+(.*?)\s*$", msg)

        if match:
            to = match.group(1)
            text = match.group(2)
        else:
            to = None
            text = msg

        if not self.only_nicks or user in self.only_nicks:
            self.brain.learn(text)

        if to == conn.nickname:
            reply = self.brain.reply(text)
            conn.privmsg(event.target, "%s: %s" % (user, reply))


class Runner:
    def run(self, brain, args):
        if len(args.password) > 0:
            servers = [ irc.bot.ServerSpec(args.server, port=args.port, password=args.password), ]
        else:
            servers = [ irc.bot.ServerSpec(args.server, port=args.port), ]
        bot = Bot(brain, servers, args.nick, args.channel, args.log_channel,
                  args.ignored_nicks, args.only_nicks)
        log.info("connected to %s:%s", args.server, args.port)

        bot.start()


class IrcLogHandler(logging.Handler):
    def __init__(self, connection, channel):
        logging.Handler.__init__(self)

        self.connection = connection
        self.channel = channel

    def emit(self, record):
        conn = self.connection

        if conn.is_connected():
            conn.privmsg(self.channel, record.getMessage())
