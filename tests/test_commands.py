import unittest

from cobe.commands import LearnIrcLogCommand

class testIrcLogParsing(unittest.TestCase):
    def setUp(self):
        self.command = LearnIrcLogCommand()

    def testNonPubmsg(self):
        msg = "this is some non-pubmsg text found in a log"
        cmd = self.command

        self.assertEqual(None, cmd._parse_irc_message(msg))
        self.assertEqual(None, cmd._parse_irc_message(msg, logformat="weechat"))

    def testNormalPubmsg(self):
        msg = "12:00 <foo> bar baz"
        cmd = self.command

        self.assertEqual("bar baz", cmd._parse_irc_message(msg)[1])

    def testPubmsgToCobe(self):
        msg = "12:00 <foo> cobe: bar baz"
        cmd = self.command

        self.assertEqual(("cobe", "bar baz"), cmd._parse_irc_message(msg))

    def testNormalPubmsgWithSpaces(self):
        msg = "12:00 < foo> bar baz"
        cmd = self.command

        self.assertEqual("bar baz", cmd._parse_irc_message(msg)[1])

    def testKibotQuotePubmsg(self):
        msg = "12:00 <foo> \"bar baz\" --user, 01-oct-09"
        cmd = self.command

        self.assertEqual("bar baz", cmd._parse_irc_message(msg)[1])

    def testIgnoredNickPubmsg(self):
        msg = "12:00 <foo> bar baz"
        cmd = self.command

        self.assertEqual(None, cmd._parse_irc_message(msg, ["foo"]))

    def testIgnoredContextMsgWeechat(self):
        msg1 = "2016-04-26 18:47:41	<--	darko (~darko@unaffiliated/darko) has quit (Remote host closed the connection)"
        msg2 = "2016-04-26 19:31:26	-->	alisor (~alisor@unaffiliated/alisor) has joined #cobe"
        msg3 = "2016-04-26 18:58:26	--	DoB is now known as DoB_away"
        cmd = self.command

        self.assertEqual(None, cmd._parse_irc_message(msg1, logformat="weechat"))
        self.assertEqual(None, cmd._parse_irc_message(msg2, logformat="weechat"))
        self.assertEqual(None, cmd._parse_irc_message(msg3, logformat="weechat"))

    def testNormalPubmsgWeechat(self):
        msg = "2016-04-27 08:42:08	foo	bar baz"
        cmd = self.command

        self.assertEqual("bar baz", cmd._parse_irc_message(msg, logformat="weechat")[1])

    def testPubmsgToCobeWeechat(self):
        msg = "2016-04-27 08:49:43	foo	cobe: bar baz"
        cmd = self.command

        self.assertEqual(("cobe", "bar baz"), cmd._parse_irc_message(msg, logformat="weechat"))

if __name__ == '__main__':
    unittest.main()
