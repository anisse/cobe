import unittest

from halng.commands import LearnIrcLogCommand

class testIrcLogParsing(unittest.TestCase):
    def setUp(self):
        self.command = LearnIrcLogCommand()

    def testNonPubmsg(self):
        msg = "this is some non-pubmsg text found in a log"
        cmd = self.command

        self.assertEqual(None, cmd._parse_irc_message(msg))

    def testNormalPubmsg(self):
        msg = "12:00 <foo> bar baz"
        cmd = self.command

        self.assertEqual("bar baz", cmd._parse_irc_message(msg))

    def testKibotQuotePubmsg(self):
        msg = "12:00 <foo> \"bar baz\" --user, 01-oct-09"
        cmd = self.command

        self.assertEqual("bar baz", cmd._parse_irc_message(msg))

if __name__ == '__main__':
    unittest.main()