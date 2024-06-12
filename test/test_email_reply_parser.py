import os
import sys
import unittest
import logging

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, "..")
sys.path.append(root)
from mailparser_reply import EmailReplyParser
from mailparser_reply.constants import MAIL_LANGUAGE_DEFAULT

COMMON_FIRST_FRAGMENT = "Fusce bibendum, quam hendrerit sagittis tempor, dui turpis tempus erat, pharetra sodales ante sem sit amet metus.\n\
Nulla malesuada, orci non vulputate lobortis, massa felis pharetra ex, convallis consectetur ex libero eget ante.\n\
Nam vel turpis posuere, rhoncus ligula in, venenatis orci. Duis interdum venenatis ex a rutrum.\n\
Duis ut libero eu lectus consequat consequat ut vel lorem. Vestibulum convallis lectus urna,\n\
et mollis ligula rutrum quis. Fusce sed odio id arcu varius aliquet nec nec nibh."


class EmailMessageTest(unittest.TestCase):
    def test_simple_body(self):
        mail = self.get_email("email_1_1", parse=True, languages=["en"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("riak-users" in mail.replies[0].content)
        self.assertTrue("riak-users" in mail.replies[0].signatures)
        self.assertTrue("riak-users" not in mail.replies[0].body)

    def test_simple_quoted_body(self):
        mail = self.get_email("email_1_3", parse=True, languages=["en"])
        self.assertEqual(3, len(mail.replies))
        self.assertTrue(
            "On 01/03/11 7:07 PM, Russell Brown wrote:" in mail.replies[1].content
        )
        self.assertTrue(
            "On 01/03/11 7:07 PM, Russell Brown wrote:" not in mail.replies[1].body
        )
        self.assertTrue("-Abhishek Kona" in mail.replies[0].signatures)
        self.assertTrue("-Abhishek Kona" not in mail.replies[0].body)

        self.assertTrue("> Hi," == mail.replies[1].body)
        # test if matching quoted signatures works
        self.assertTrue(">> -Abhishek Kona" in mail.replies[2].content)
        self.assertTrue(">> -Abhishek Kona" in mail.replies[2].signatures)
        self.assertTrue(">> -Abhishek Kona" not in mail.replies[2].body)

    def test_simple_scrambled_body(self):
        mail = self.get_email("email_1_4", parse=True, languages=["en"])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("defunkt<reply@reply.github.com>" in mail.replies[1].content)
        self.assertTrue("defunkt<reply@reply.github.com>" in mail.replies[1].headers)

    def test_simple_longer_mail(self):
        mail = self.get_email("email_1_5", parse=True, languages=["en", "de", "david"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue(len(mail.latest_reply.split("\n")) == 15)

    def test_simple_scrambled_header(self):
        mail = self.get_email("email_1_6", parse=True, languages=["en"])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("<reply@reply.github.com>" in mail.replies[1].headers)

    def test_simple_scrambled_header2(self):
        mail = self.get_email("email_1_7", parse=True, languages=["en"])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("<notifications@github.com>wrote:" in mail.replies[1].headers)

    def test_simple_quoted_reply(self):
        mail = self.get_email("email_1_8", parse=True, languages=["en"])
        # TODO: Should this *actually* be the desired behaviour? tbh, nobody sends mails including this header tho
        #   Maybe otherwise: 1) Negative lookahead unquoted message
        #                    2) Unless message is disclaimer/signature (scan from behind)
        self.assertEqual(2, len(mail.replies))
        # self.assertTrue("--\nHey there, this is my signature" == mail.replies[1].signatures)

    def test_gmail_header(self):
        mail = self.get_email("email_2_1", parse=True, languages=["en"])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue(
            "Outlook with a reply\n\n\n------------------------------"
            == mail.replies[0].body
        )
        self.assertTrue(
            "Google Apps Sync Team [mailto:mail-noreply@google.com]"
            in mail.replies[1].headers
        )
        self.assertTrue(
            "Google Apps Sync Team [mailto:mail-noreply@google.com]"
            not in mail.replies[1].body
        )

    def test_gmail_indented(self):
        mail = self.get_email("email_2_3", parse=True, languages=["en"])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue(
            "Outlook with a reply above headers using unusual format"
            == mail.replies[0].body
        )
        # _normalize_body flattens the lines
        self.assertTrue(
            "Ei tale aliquam eum, at vel tale sensibus, an sit vero magna. Vis no veri"
            in mail.replies[1].body
        )

    def test_complex_mail_thread(self):
        mail = self.get_email("email_3_1", parse=True, languages=["en", "de", "david"])
        self.assertEqual(5, len(mail.replies))

    def test_multiline_on(self):
        mail = self.get_email("multiline_on", parse=True, languages=["en", "de"])
        self.assertEqual(4, len(mail.replies))

    def test_header_no_delimiter(self):
        mail = self.get_email(
            "email_headers_no_delimiter",
            parse=True,
            languages=[
                "en",
            ],
        )
        self.assertEqual(3, len(mail.replies))
        self.assertTrue("And another reply!" == mail.replies[0].body)
        self.assertTrue("A reply" == mail.replies[1].body)
        self.assertTrue("--\nSent from my iPhone" == mail.replies[1].signatures)
        self.assertTrue(
            "This is a message.\nWith a second line." == mail.replies[2].body
        )

    def test_sent_from_junk1(self):
        mail = self.get_email("email_sent_from_iPhone", parse=True, languages=["en"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email" == mail.replies[0].body)
        self.assertTrue("Sent from my iPhone" == mail.replies[0].signatures)

    def test_sent_from_junk2(self):
        mail = self.get_email(
            "email_sent_from_multi_word_mobile_device", parse=True, languages=["en"]
        )
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email" == mail.replies[0].body)
        self.assertTrue(
            "Sent from my Verizon Wireless BlackBerry" == mail.replies[0].signatures
        )

    def test_sent_from_junk3(self):
        mail = self.get_email(
            "email_sent_from_BlackBerry", parse=True, languages=["en"]
        )
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email" == mail.replies[0].body)
        self.assertTrue("Sent from my BlackBerry" == mail.replies[0].signatures)

    def test_sent_from_junk4(self):
        mail = self.get_email(
            "email_sent_from_not_signature", parse=True, languages=["en"]
        )
        self.assertEqual(1, len(mail.replies))
        self.assertTrue(
            "Here is another email\n\nSent from my desk, is much easier than my mobile phone."
            == mail.replies[0].body
        )
        self.assertTrue("" == mail.replies[0].signatures)

    def test_ja_simple_body(self):
        mail = self.get_email("email_ja_1_1", parse=True, languages=["ja"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("こんにちは" in mail.replies[0].body)

    def test_ja_simple_quoted_reply(self):
        mail = self.get_email("email_ja_1_2", parse=True, languages=["ja"])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("お世話になっております。織田です。" in mail.replies[0].body)
        self.assertTrue("それでは 11:00 にお待ちしております。" in mail.replies[0].body)
        self.assertTrue("かしこまりました" in mail.replies[1].body)
        self.assertTrue("明日の 11:00 でお願いいたします" in mail.replies[1].body)

    def test_pl_simple_body(self):
        mail = self.get_email("email_pl_1_1", parse=True, languages=["pl"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Czesc Anno" in mail.replies[0].body)
        self.assertTrue("Pozdrawiam,\nJan" in mail.replies[0].signatures)
        self.assertTrue("Pozdrawiam,\nJan" not in mail.replies[0].body)

    def test_pl_simple_quoted_reply(self):
        mail = self.get_email("email_pl_1_2", parse=True, languages=["pl"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue(
            "Dnia 28 lutego 2023 14:00 Anna Nowak <anna.nowak@example.com>"
            in mail.replies[0].content
        )
        self.assertTrue(
            "Dnia 28 lutego 2023 14:00 Anna Nowak <anna.nowak@example.com>"
            not in mail.replies[0].body
        )
        self.assertTrue("> Pozdrawiam," in mail.replies[0].content)
        self.assertTrue("> Pozdrawiam," in mail.replies[0].signatures)
        self.assertTrue("> Pozdrawiam," not in mail.replies[0].body)

    def test_pl_simple_signature(self):
        mail = self.get_email("email_pl_1_3", parse=True, languages=["pl"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Z powazaniem,\nJan" in mail.replies[0].signatures)
        self.assertTrue("Z powazaniem,\nJan" not in mail.replies[0].body)

    def test_email_zoho(self):
        mail = self.get_email("email_zoho", parse=True, languages=["en"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue(
            "What is the best way to clear a Riak bucket of all key, values after\nrunning a test?\n"
            in mail.replies[0].content
        )

    def test_email_emoji(self):
        mail = self.get_email("email_emoji", parse=True, languages=["en"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue(
            "🎉\n\n—\nJohn Doe\nCEO at Pandaland\n\n@pandaland"
            in mail.replies[0].content
        )

    def test_en_multiline_2(self):
        mail = self.get_email("email_en_multiline_2", parse=True, languages=["en"])
        self.assertEqual(2, len(mail.replies))
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].content)

    def test_email_finnish(self):
        mail = self.get_email("email_finnish", parse=True, languages=["en"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue(COMMON_FIRST_FRAGMENT in mail.replies[0].content)

    def test_email_fr_multiline(self):
        mail = self.get_email("email_fr_multiline", parse=True, languages=["fr"])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue(COMMON_FIRST_FRAGMENT, mail.replies[0].content)

    def test_email_gmail_split_line_from(self):
        mail = self.get_email(
            "email_gmail_split_line_from", parse=True, languages=["en"]
        )
        self.assertEqual(2, len(mail.replies))
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].content)

    def test_email_ios_outlook(self):
        mail = self.get_email("email_ios_outlook", parse=True, languages=["en"])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue(COMMON_FIRST_FRAGMENT in mail.replies[0].content)
        self.assertTrue(
            "From: The Hiring Engine <job-applicant-incoming-text+65701@hiringenginemail.com>\n"
            in mail.replies[1].headers
        )

    def test_email_iphone(self):
        mail = self.get_email("email_iphone", parse=True, languages=["en"])
        self.assertEqual(1, len(mail.replies))
        self.assertEqual(
            "Here is another email\n\nSent from my iPhone", mail.replies[0].content
        )
        self.assertEqual("Sent from my iPhone", mail.replies[0].signatures)

    def test_email_msn(self):
        mail = self.get_email("email_msn", parse=True, languages=["en"])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue(COMMON_FIRST_FRAGMENT in mail.replies[0].content)

    def test_email_norwegian_gmail(self):
        mail = self.get_email("email_norwegian_gmail", parse=True, languages=["en"])
        self.assertEqual(3, len(mail.replies))
        self.assertTrue(COMMON_FIRST_FRAGMENT in mail.replies[0].content)

    def test_email_outlook_split_line_from(self):
        mail = self.get_email(
            "email_outlook_split_line_from", parse=True, languages=["en"]
        )
        self.assertEqual(2, len(mail.replies))
        self.assertTrue(COMMON_FIRST_FRAGMENT in mail.replies[0].content)

    def test_email_reply_header(self):
        mail = self.get_email("email_reply_header", parse=True, languages=["en"])
        self.assertEqual(3, len(mail.replies))
        self.assertTrue("On the other hand" in mail.replies[0].content)
        self.assertTrue("On Wed, Dec 9" in mail.replies[1].content)
        self.assertEqual(
            "On Wed, Dec 9, Mister Example\n<mrmister@example.com>\nwrote:",
            mail.replies[1].headers,
        )
        self.assertEqual(
            "> On Tue, 2011-03-01 at 18:02 +0530, Stranger Jones wrote:",
            mail.replies[2].headers,
        )

    def test_email_sent_from(self):
        mail = self.get_email("email_sent_from", parse=True, languages=["en"])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue(
            "Hi it can happen to any texts you type, as long as you type in between words or paragraphs.\n"
            in mail.replies[0].content
        )

    def test_email_thread(self):
        mail = self.get_email("email_thread", parse=True, languages=["en"])
        self.assertEqual(3, len(mail.replies))
        self.assertEqual(
            "This is new email reply in thread from bellow.\n\nOn Nov 21, 2014,\nat 10:18,\nJohn Doe "
            "<john@doe123.com> wrote:\n\n> Ok. Thanks.\n>",
            mail.replies[0].content,
        )
        self.assertEqual(
            "> On Nov 21, 2014, at 9:26, Jim Beam <jim@beam123.com> wrote:",
            mail.replies[1].headers,
        )
        self.assertEqual(
            ">> --\n>> Jim Beam – Acme Corp\n>>\n>", mail.replies[2].signatures
        )

    def get_email(self, name: str, parse: bool = True, languages: list = None):
        """Return EmailMessage instance or text content"""
        with open(f"test/emails/{name}.txt") as f:
            text = f.read()
        return (
            EmailReplyParser(languages=languages or [MAIL_LANGUAGE_DEFAULT]).read(text)
            if parse
            else text
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    unittest.main()
