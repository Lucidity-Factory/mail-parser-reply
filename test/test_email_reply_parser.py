import os
import sys
import unittest
import logging

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sys.path.append(root)
from mailparser_reply import EmailReplyParser, EmailMessage
from mailparser_reply.constants import MAIL_LANGUAGE_DEFAULT

#: Shared first-reply body used across fixtures ported from crisp-oss/email-reply-parser
COMMON_FIRST_FRAGMENT = (
    "Fusce bibendum, quam hendrerit sagittis tempor, dui turpis tempus erat, pharetra sodales ante sem sit amet metus.\n"
    "Nulla malesuada, orci non vulputate lobortis, massa felis pharetra ex, convallis consectetur ex libero eget ante.\n"
    "Nam vel turpis posuere, rhoncus ligula in, venenatis orci. Duis interdum venenatis ex a rutrum.\n"
    "Duis ut libero eu lectus consequat consequat ut vel lorem. Vestibulum convallis lectus urna,\n"
    "et mollis ligula rutrum quis. Fusce sed odio id arcu varius aliquet nec nec nibh."
)


class EmailMessageTest(unittest.TestCase):
    def test_simple_body(self):
        mail = self.get_email('email_1_1', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("riak-users" in mail.replies[0].content)
        self.assertTrue("riak-users" in mail.replies[0].signatures)
        self.assertTrue("riak-users" not in mail.replies[0].body)

    def test_simple_quoted_body(self):
        mail = self.get_email('email_1_3', parse=True, languages=['en'])
        self.assertEqual(3, len(mail.replies))
        self.assertTrue("On 01/03/11 7:07 PM, Russell Brown wrote:" in mail.replies[1].content)
        self.assertTrue("On 01/03/11 7:07 PM, Russell Brown wrote:" not in mail.replies[1].body)
        self.assertTrue("-Abhishek Kona" in mail.replies[0].signatures)
        self.assertTrue("-Abhishek Kona" not in mail.replies[0].body)

        self.assertTrue("> Hi," == mail.replies[1].body)
        # test if matching quoted signatures works
        self.assertTrue(">> -Abhishek Kona" in mail.replies[2].content)
        self.assertTrue(">> -Abhishek Kona" in mail.replies[2].signatures)
        self.assertTrue(">> -Abhishek Kona" not in mail.replies[2].body)

    def test_hyphen_signature(self):
        mail = self.get_email('email_1_1', parse=True, languages=['en'])

        # interpret hyphen as signature
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("-Abhishek Kona" in mail.replies[0].signatures)

    def test_keep_hyphen_lists(self):
        text = self.get_email('email_1_1', parse=False)
        mail = EmailMessage(
            text=text,
            languages=[MAIL_LANGUAGE_DEFAULT],
            keep_hyphen_lists=True
        )
        mail.read()

        # interpret hyphen as body
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("-Abhishek Kona" not in mail.replies[0].signatures)

    def test_simple_scrambled_body(self):
        mail = self.get_email('email_1_4', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("defunkt<reply@reply.github.com>" in mail.replies[1].content)
        self.assertTrue("defunkt<reply@reply.github.com>" in mail.replies[1].headers)

    def test_simple_longer_mail(self):
        mail = self.get_email('email_1_5', parse=True, languages=['en', 'de', 'david'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue(len(mail.latest_reply.split('\n')) == 15)

    def test_simple_scrambled_header(self):
        mail = self.get_email('email_1_6', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("<reply@reply.github.com>" in mail.replies[1].headers)

    def test_simple_scrambled_header2(self):
        mail = self.get_email('email_1_7', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("<notifications@github.com>wrote:" in mail.replies[1].headers)

    def test_simple_quoted_reply(self):
        mail = self.get_email('email_1_8', parse=True, languages=['en'])
        # TODO: Should this *actually* be the desired behaviour? tbh, nobody sends mails including this header tho
        #   Maybe otherwise: 1) Negative lookahead unquoted message
        #                    2) Unless message is disclaimer/signature (scan from behind)
        self.assertEqual(2, len(mail.replies))
        # self.assertTrue("--\nHey there, this is my signature" == mail.replies[1].signatures)

    def test_gmail_header(self):
        mail = self.get_email('email_2_1', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("Outlook with a reply\n\n\n------------------------------" == mail.replies[0].body)
        self.assertTrue("Google Apps Sync Team [mailto:mail-noreply@google.com]" in mail.replies[1].headers)
        self.assertTrue("Google Apps Sync Team [mailto:mail-noreply@google.com]" not in mail.replies[1].body)

    def test_gmail_indented(self):
        mail = self.get_email('email_2_3', parse=True, languages=['en'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("Outlook with a reply above headers using unusual format" == mail.replies[0].body)
        # _normalize_body flattens the lines
        self.assertTrue("Ei tale aliquam eum, at vel tale sensibus, an sit vero magna. Vis no veri" in mail.replies[1].body)

    def test_complex_mail_thread(self):
        mail = self.get_email('email_3_1', parse=True, languages=['en', 'de', 'david'])
        self.assertEqual(5, len(mail.replies))

    def test_multiline_on(self):
        mail = self.get_email('multiline_on', parse=True, languages=['en', 'de'])
        self.assertEqual(4, len(mail.replies))

    def test_header_no_delimiter(self):
        mail = self.get_email('email_headers_no_delimiter', parse=True, languages=['en',])
        self.assertEqual(3, len(mail.replies))
        self.assertTrue("And another reply!" == mail.replies[0].body)
        self.assertTrue("A reply" == mail.replies[1].body)
        self.assertTrue("--\nSent from my iPhone" == mail.replies[1].signatures)
        self.assertTrue("This is a message.\nWith a second line." == mail.replies[2].body)

    def test_sent_from_junk1(self):
        mail = self.get_email('email_sent_from_iPhone', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email" == mail.replies[0].body)
        self.assertTrue("Sent from my iPhone" == mail.replies[0].signatures)

    def test_sent_from_junk2(self):
        mail = self.get_email('email_sent_from_multi_word_mobile_device', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email" == mail.replies[0].body)
        self.assertTrue("Sent from my Verizon Wireless BlackBerry" == mail.replies[0].signatures)

    def test_sent_from_junk3(self):
        mail = self.get_email('email_sent_from_BlackBerry', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email" == mail.replies[0].body)
        self.assertTrue("Sent from my BlackBerry" == mail.replies[0].signatures)

    def test_sent_from_junk4(self):
        mail = self.get_email('email_sent_from_not_signature', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Here is another email\n\nSent from my desk, is much easier than my mobile phone." == mail.replies[0].body)
        self.assertTrue("" == mail.replies[0].signatures)

    def test_ja_simple_body(self):
        mail = self.get_email('email_ja_1_1', parse=True, languages=['ja'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("こんにちは" in mail.replies[0].body)

    def test_ja_simple_quoted_reply(self):
        mail = self.get_email('email_ja_1_2', parse=True, languages=['ja'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("お世話になっております。織田です。" in mail.replies[0].body)
        self.assertTrue("それでは 11:00 にお待ちしております。" in mail.replies[0].body)
        self.assertTrue("かしこまりました" in mail.replies[1].body)
        self.assertTrue("明日の 11:00 でお願いいたします" in mail.replies[1].body)


    # Dutch language
    def test_dutch_simple_body(self):
        mail = self.get_email('email_nl_1_1', parse=True, languages=['nl'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("riak-gebruikers" in mail.replies[0].content)
        self.assertTrue("riak-gebruikers" in mail.replies[0].signatures)
        self.assertTrue("riak-gebruikers" not in mail.replies[0].body)

    def test_dutch_gmail_header(self):
        mail = self.get_email('email_nl_1_2', parse=True, languages=['nl'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("Outlook met een antwoord\n\n\n------------------------------" == mail.replies[0].body)
        self.assertTrue("Google Apps Sync Team [mailto:mail-noreply@google.com]" in mail.replies[1].headers)
        self.assertTrue("Google Apps Sync Team [mailto:mail-noreply@google.com]" not in mail.replies[1].body)

    def test_pl_simple_body(self):
        mail = self.get_email('email_pl_1_1', parse=True, languages=['pl'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Czesc Anno" in mail.replies[0].body)
        self.assertTrue("Pozdrawiam,\nJan" in mail.replies[0].signatures)
        self.assertTrue("Pozdrawiam,\nJan" not in mail.replies[0].body)

    def test_pl_simple_quoted_reply(self):
        mail = self.get_email('email_pl_1_2', parse=True, languages=['pl'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("Dnia 28 lutego 2023 14:00 Anna Nowak <anna.nowak@example.com>" in mail.replies[1].content)
        self.assertTrue("Dnia 28 lutego 2023 14:00 Anna Nowak <anna.nowak@example.com>" not in mail.replies[1].body)
        self.assertTrue("> Pozdrawiam," in mail.replies[1].content)
        self.assertTrue("> Pozdrawiam," in mail.replies[1].signatures)
        self.assertTrue("> Pozdrawiam," not in mail.replies[1].body)

    def test_pl_simple_signature(self):
        mail = self.get_email('email_pl_1_3', parse=True, languages=['pl'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Z powazaniem,\nJan" in mail.replies[0].signatures)
        self.assertTrue("Z powazaniem,\nJan" not in mail.replies[0].body)

    def test_header_begins_w_signature(self):
        mail = self.get_email('begins_with_signature', parse=True, languages=['en'])
        self.assertTrue(mail.replies[0].signatures. startswith("Regards,"))

    def test_swedish_simple_body(self):
        mail = self.get_email('email_swedish_2', parse=True, languages=['sv'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue("Hello Anna," in mail.replies[0].body)
        self.assertTrue("/John" in mail.replies[0].signatures)
        self.assertTrue("/John" not in mail.replies[0].body)

    def test_swedish_quoted_reply(self):
        mail = self.get_email('email_swedish_1', parse=True, languages=['sv'])
        self.assertEqual(2, len(mail.replies))
        self.assertIn("Ursäkta mitt sena svar!", mail.replies[0].body)
        self.assertIn("Hej Person B,", mail.replies[1].body)
        self.assertIn("Med Vänlig Hälsning,", mail.replies[1].body)

    def test_swedish_realistic_anonymized(self):
        mail = self.get_email('email_sv_anon_1', parse=True, languages=['sv'])
        self.assertEqual(3, len(mail.replies))
        self.assertIn("Berättar gärna.", mail.replies[0].body)
        self.assertIn("Kan inte se att det står något", mail.replies[1].body)
        self.assertIn("Jag har försökt få tag", mail.replies[2].body)

    def test_danish_simple_body(self):
        mail = self.get_email('email_danish_1', parse=True, languages=['da'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("Hej Peter," in mail.replies[0].body)
        self.assertTrue("Med venlig hilsen\nAnders Andersen" in mail.replies[0].signatures)
        self.assertTrue("Med venlig hilsen\nAnders Andersen" not in mail.replies[0].body)
        self.assertTrue("Hej Anders," in mail.replies[1].body)
        self.assertTrue("> Mvh\n> Peter" in mail.replies[1].signatures)

    def test_danish_outlook_header(self):
        mail = self.get_email('email_danish_2', parse=True, languages=['da'])
        self.assertEqual(2, len(mail.replies))
        self.assertTrue("Jeg har modtaget filerne." in mail.replies[0].body)
        self.assertTrue("Hilsen\nSøren" in mail.replies[0].signatures)
        self.assertTrue("Her er filerne du bad om." in mail.replies[1].body)
        self.assertTrue("Mvh\nHanne" in mail.replies[1].signatures)

    def test_danish_gmail_header(self):
        mail = self.get_email('email_danish_3', parse=True, languages=['da'])
        self.assertEqual(2, len(mail.replies))
        self.assertIn("Svar.", mail.replies[0].body)
        self.assertIn("Hej", mail.replies[1].body)

    def test_danish_outlook_separator(self):
        mail = self.get_email('email_danish_4', parse=True, languages=['da'])
        self.assertEqual(2, len(mail.replies))
        self.assertIn("Svar.", mail.replies[0].body)
        # Verify separator is removed/handled
        self.assertNotIn("-----Oprindelig meddelelse-----", mail.replies[0].body)
        self.assertIn("Hej", mail.replies[1].body)

    def test_danish_signatures_short(self):
        mail = self.get_email('email_danish_5', parse=True, languages=['da'])
        self.assertEqual(1, len(mail.replies))
        self.assertIn("Svar.", mail.replies[0].body)
        self.assertIn("Kh\nPeter", mail.replies[0].signatures)
        self.assertNotIn("Kh\nPeter", mail.replies[0].body)

    # --- Patterns ported from crisp-oss/email-reply-parser ---
    def test_crisp_original_message(self):
        # Existing "----- Original Message -----" separator — regression
        mail = self.get_email('email_crisp_original_message', parse=True, languages=['en'])
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].body)
        self.assertTrue(any('original message' in r.content.lower() for r in mail.replies[1:]))

    def test_crisp_original_message_2(self):
        # Existing "----- Original Message -----" separator — regression
        mail = self.get_email('email_crisp_original_message_2', parse=True, languages=['en'])
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].body)
        self.assertTrue(any('Original Message' in r.content for r in mail.replies[1:]))

    def test_crisp_fr_separator(self):
        # New: "-------- Message d'origine --------" separator
        mail = self.get_email('email_crisp_fr_separator', parse=True, languages=['en'])
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].body)
        self.assertTrue(any("Message d'origine" in r.content for r in mail.replies[1:]))

    def test_crisp_de_outlook_separator(self):
        # New: "-----Ursprüngliche Nachricht-----" separator
        mail = self.get_email('email_crisp_de_outlook', parse=True, languages=['de'])
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].body)
        self.assertTrue(any('Urspr\u00fcngliche Nachricht' in r.content for r in mail.replies[1:]))

    def test_crisp_da_separator(self):
        # New: "-------- Oprindelig Besked --------" separator (language-independent)
        mail = self.get_email('email_crisp_da_separator', parse=True, languages=['en'])
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].body)
        self.assertTrue(any('Oprindelig' in r.content for r in mail.replies[1:]))

    def test_crisp_en_multiline_wrote(self):
        # New: "On ... <...>\nwrote:" spans a newline (Outlook/iOS wrap)
        mail = self.get_email('email_crisp_en_multiline_2', parse=True, languages=['en'])
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].body)
        self.assertTrue('wrote:' in mail.replies[1].headers)

    def test_crisp_fr_multiline(self):
        # New: "Le ... <...>\na écrit :" spans a newline
        mail = self.get_email('email_crisp_fr_multiline', parse=True, languages=['fr'])
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].body)
        self.assertTrue('\n' in mail.replies[1].headers)
        self.assertTrue('a \u00e9crit' in mail.replies[1].headers)

    def test_crisp_fr_quoted(self):
        # Regression: single-line "Le ... a écrit:" still matches after multi-line rewrite
        mail = self.get_email('email_crisp_fr_2', parse=True, languages=['fr'])
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].body)
        self.assertTrue('a \u00e9crit' in mail.replies[1].headers)

    def test_crisp_fr_ios_outlook(self):
        # New: "Envoyé à partir de Outlook pour iOS<...>" caught as sent_from signature
        mail = self.get_email('email_crisp_fr_ios', parse=True, languages=['fr', 'en'])
        self.assertEqual(COMMON_FIRST_FRAGMENT, mail.replies[0].body)
        self.assertTrue('Envoy\u00e9 \u00e0 partir de' in mail.replies[0].signatures)

    def test_crisp_cheers_signature(self):
        # New EN "Cheers,?!?" signature — covers the case of a sign-off with
        # no trailing comma/bang (e.g. "Cheers 🎉").
        mail = self.get_email('email_crisp_cheers', parse=True, languages=['en'])
        self.assertEqual(1, len(mail.replies))
        self.assertTrue('Cheers' in mail.replies[0].signatures)
        self.assertTrue('Sarah Johnson' in mail.replies[0].signatures)
        self.assertTrue('Thanks for the update!' in mail.replies[0].body)
        self.assertTrue('Cheers' not in mail.replies[0].body)

    def get_email(self, name: str, parse: bool = True, languages: list = None):
        """ Return EmailMessage instance or text content """
        with open(f'test/emails/{name}.txt', encoding='utf-8') as f:
            text = f.read()
        return EmailReplyParser(
            languages=languages or [MAIL_LANGUAGE_DEFAULT]
        ).read(text) if parse else text


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    unittest.main()
