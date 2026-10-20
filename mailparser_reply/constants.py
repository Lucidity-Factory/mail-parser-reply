from typing import Dict

#: Fallback language if no other language is specified
MAIL_LANGUAGE_DEFAULT = 'en'

#: Matches text-mail quotation (usually starting with ">");
#: resulting in "> Hello world"
QUOTED_REGEX = r'(>+)'
#: Regex to remove all leading quotations
QUOTED_REMOVAL_REGEX = r'^(> *)'
#: Allow to match within (multi)-quoted body
#: e.g. allowing regex to match *inside* lines starting with "> > ..."
QUOTED_MATCH_INCLUDE = r'(?:> ?)*'
#: Gap between a quote header's start word and its verb, e.g. "On" ... "wrote:": at least two
#: characters on at most two lines, never a blank line. Written so that each text has one way to
#: match: two adjacent lazy runs (.+?\s?.+?) made a long line starting with the start word
#: quadratic to reject (for de and sv, a long line after the verb).
WRAPPED_GAP = r'(?:[^\n](?:[^\n]*\n)??[^\n]+?)'

#: Outlook-style mail separator (32 underscores); also occasionally
#: used within signatures
OUTLOOK_MAIL_SEPARATOR = r'(\n{2,} ?[_-]{32,})'
#: Common mail separators (+ old Outlook separator). Covers EN/DA/FR/DE variants
#: such as "----- Original Message -----", "-------- Oprindelig Besked --------",
#: "-------- Message d'origine --------", and "-----Ursprüngliche Nachricht-----".
#: Also forward separators: Gmail's "---------- Forwarded message ---------" and
#: Zoho's "============ Forwarded Message ============" (matched case-insensitively, so
#: "----- Forwarded Message -----" and similar variants match too). Outlook's line of 32 or
#: more underscores counts only when the next line starts with "From:" ("*From:*" and
#: "From :" too; case-sensitive), the only label seen after it in real mail, so underscore
#: lines followed by "Website:", "Tel:" or plain text, as in signatures or meeting invites,
#: are left alone. An underscore line after a blank line is already removed by
#: EmailMessage._normalize_text, so this applies to one directly under the text.
GENERIC_MAIL_SEPARATOR = (
    r"^(?:-{5,} ?(?:Original Message|Oprindelig Besked|"
    r"Message d['\u2019]origine|Urspr\u00fcngliche Nachricht|Forwarded message) ?-{5,}|"
    r"={5,} ?Forwarded Message ?={5,}|_{32,}(?=\n[* ]*(?-i:From) ?:))$"
)

#: Outlook Signature defaults; line optionally starts with whitespace, contains two
#: hyphens or underscores, and ends with optional whitespace.
#   1) -- \nJohn Doe
#   2) -John Doe
DEFAULT_SIGNATURE_REGEX = rf'\s*^{QUOTED_MATCH_INCLUDE}(?:[-_]{{2}}\n|- ?\w).*'

#: Same as above except it won't capture hyphen marked lists like
# - one
# - two
NOLIST_SIGNATURE_REGEX = rf'\s*^{QUOTED_MATCH_INCLUDE}(?:[-_]{{2}}\n).*'

#: All kinds of whitespaces incl special characters; used for Disclaimers, because they
#: are usually either added in post by a mailserver or scrambled due to their higher complexity.
SINGLE_SPACE_VARIATIONS = r'[ \u200b\xA0\t]'
#: Linebreaks ok too
OPTIONAL_LINEBREAK = rf'[,()]?{SINGLE_SPACE_VARIATIONS}{{0,3}}[\n\r]?{SINGLE_SPACE_VARIATIONS}{{0,3}}[,()]?'
#: Possible ways to check for linebreaks
SENTENCE_START = rf'(?:[\n\r.!?]|^){SINGLE_SPACE_VARIATIONS}{{0,3}}'

#: Matching regex for all languages
MAIL_LANGUAGES: Dict[str, Dict[str, str]] = {
    'en': {
        # Apple Mail-style header
        # ^(?!On[.\s]*On\s(.+?\s?.+?)\swrote:) – Negative lookahead, see:
        #    https://github.com/github/email_reply_parser/pull/31
        # <QUOTED_MATCH_INCLUDE> – allow matching this inside quoted levels
        # On\s<WRAPPED_GAP>\s?wrote: – match "On 01.01.2025, John Doe wrote:"
        #   See multiline_on.txt for example data
        # Mail.ru / myMail header: "Monday, 8 June 2026, 10:15PM +01:00 from <addr>:"; the client
        #   may put its "sent from" advert on the same line first, so the rest of the line before
        #   the date belongs to the header (at most 200 characters of it). Date, UTC offset,
        #   " from ", an address (no space around the "@") and the final colon must all be present;
        #   no other colon may follow " from ", so the match cannot run on into another date.
        #   See email_mailru_advert_inline.txt / email_mailru_advert_own_line.txt for example data
        'wrote_header': r'^(?!On[.\s]*On\s(' + WRAPPED_GAP + r')\swrote:)(' + QUOTED_MATCH_INCLUDE + r'On\s' + WRAPPED_GAP + r'\s?wrote:)$'
                        + r'|^(' + QUOTED_MATCH_INCLUDE + r'[^\n]{0,200}?(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day, '
                        + r'\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November'
                        + r'|December) \d{4}, \d{1,2}:\d{2}\s?(?:[AP]M|[ap]\.m\.)? [+-]\d{2}:\d{2} '
                        + r'from [^\n@:]{0,80}[^\s@:]@[^\s@:][^\n:]{0,120}:)$',
        # Outlook-style header
        # (?:(?:^|\n)[* ]*(?:From|Sent|To|Subject|Date|Cc):[ *]* – match From:/*From*:, ... headers
        # (?:\s{,2}).*){2,} – allow multi-line headers; some clients split the headers up into multiple lines.
        #       Also require at least two occurrences of the above pattern; e.g. From: ...\n Sent: ...
        # (?:\n.*){,1} – allow optional subject or other broken multi-line at the end
        # Second alternative: some webmail clients put a blank line between the fields. Only a
        #   block that starts with "From:" on a line holding an "@" and has at least two more
        #   fields, each after one blank line, counts; the labels are case-sensitive here, so prose
        #   or signature lines with these words are left alone. EN only, as only English clients
        #   have been seen doing this. See email_headers_blank_separated.txt
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:From|Sent|To|Subject|Date|Cc|Organization):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})'
                       + r'|((?:^|\n)[* ]*(?-i:From):[ *]*[^\n@]*@.*'
                       + r'(?:\n\n[* ]*(?-i:Sent|To|Subject|Date|Cc):[ *]*.*){2,})',
        'disclaimers': [
            'CAUTION:',
            'Disclaimer:',
            'Warning:',
            'Confidential:',
            'CONFIDENTIALITY:',
            r'(?:Privileged|Confidential|Private|Sensitive|Important) (?:Notice|Note|Information):',
            r'[\* ]*Disclaimer[\* ]*',
        ],
        'signatures': [
            'Best regards',
            'Kind Regards',
            'Thanks,',
            'Thank you,',
            'Best,',
            'All the best',
            'regards,',
            r'Cheers,?!?',
            # "Best wishes" — ported from crisp-oss/email-reply-parser; no fixture
            # in the upstream repo currently exercises this line.
            r'Best wishes,?!?',
        ],
        'sent_from': 'Sent from my|Get Outlook for',
    },
    'de': {
        'wrote_header': r'^(?!Am.*Am\s.+?schrieb.*:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Am\s(?:.+?\s?)schrieb\s' + WRAPPED_GAP + r':)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Von|Gesendet|An|Betreff|Datum|Cc|Organisation):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            r'(?:Wichtiger )?Hinweis:',
            'Achtung:',
        ],
        'signatures': [
            r'Mit freundlichen Gr\u00fc\u00DFen',
            r'Mit freundlichen Gr\u00fc\u00DFen / (?:Best|Kind) regards,',
            r'(?:(?:Beste(?:n)?|Liebe|Viele) )?(?:Gr(?:\u00fc|ue)(?:\u00DF|ss)(?:e)?|Gru\u00DF|Gruss)',
            # "Von <device> gesendet" — mirror of the existing "Gesendet von ..."
            # sent-from, ported from crisp-oss/email-reply-parser; no fixture
            # currently exercises this line.
            r'Von\s[^\n]+?\sgesendet',
        ],
        'sent_from': 'Gesendet von',
    },
    'cs': {
        'wrote_header': r'^(?!Dne[.\s]*Dne\s(' + WRAPPED_GAP + r')\snapsal\(a\):)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Dne\s' + WRAPPED_GAP + r'\s?napsal\(a\):)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Od|Odesláno|Komu|Předmět|Datum|Kopie):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            'Upozornění:',
            'Důvěrné:',
            'Varování:',
        ],
        'signatures': [
            'S pozdravem,',
            'S úctou,',
            'Děkuji,',
            'Děkujeme,',
            'S přáním hezkého dne,',
        ],
        'sent_from': r'Odesláno z mého.*',
    },
    'da': {
        'wrote_header': r"^(?!Den[.\s]*Den\s(.+?)\sskrev:)("
                        + QUOTED_MATCH_INCLUDE
                        + r"(?:Den|[Mm]an|[Tt]ir|[Oo]ns|[Tt]or|[Ff]re|[Ll]ør|[Ss]øn|[0-9]).+?\sskrev\s.+?:)$",
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')?-----Oprindelig meddelelse-----\n)?(?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:[Ff]ra|[Ss]endt|[Tt]il|[Ee]mne|[Dd]ato|[Cc]c|[Kk]opi|[Vv]edhæftet):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            'Advarsel:',
            'Bemærk:',
            'Fortroligt:',
        ],
        'signatures': [
            'Med venlig hilsen',
            'Venlig hilsen',
            'Hilsen',
            'Mvh',
            'Dbh',
            'Bedste hilsner',
            'De bedste hilsner',
            'Kh',
            'Knus',
            'Tak',
            'På forhånd tak',
        ],
        'sent_from': 'Sendt fra min|Sendt fra|Hent Outlook til|Sendt fra Outlook',
    },
    'es': {
        'wrote_header': r'^(?!El\s.+\s escribió:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'El\s.+\s escribió:)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:De|Enviado|Para|Asunto|Fecha|CC|Organización):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            'Aviso:',
            'Confidencialidad:',
            'Advertencia:',
            'Descargo de responsabilidad:',
        ],
        'signatures': [
            'Saludos,',
            'Atentamente,',
            'Gracias,',
            'Un saludo,',
            'Cordialmente,',
            'Muchas gracias,',
        ],
        'sent_from': r'Enviado desde mi.*',
    },
    'fi': {
        # Finnish: "<weekday abbr> <day>. <month> <year> klo <time> <name> <email> kirjoitti:"
        # Example: "pe 20. lokakuuta 2017 klo 17.50 John Coe <j@x.com> kirjoitti:"
        # The leading "\w{2,4}\s\d" matches "pe 20", "ma 1", "ke 12", etc.
        # <WRAPPED_GAP>\s?kirjoitti: bounded gap shared with the other languages: Gmail
        #   wraps the header inside the address, which the gap allows (at most three line
        #   breaks, never a blank line), so a nested older header cannot be reached and
        #   no negative lookahead is needed. See email_fi_gmail_nested.txt
        'wrote_header': r'^('
                        + QUOTED_MATCH_INCLUDE
                        + r'\w{2,4}\s\d' + WRAPPED_GAP + r'\s?kirjoitti:)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:L\u00e4hett\u00e4j\u00e4|L\u00e4hetetty|Vastaanottaja|Aihe|P\u00e4iv\u00e4m\u00e4\u00e4r\u00e4):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [],
        'signatures': [
            r'Yst\u00e4v\u00e4llisin terveisin',
            'Parhain terveisin',
            'Terveisin',
        ],
        'sent_from': r'L\u00e4hetetty',
    },
    'fr': {
        # Le\s<WRAPPED_GAP>\s?a écrit : same bounded gap as the other languages, so a
        #   wrapped header (Gmail, Outlook/iOS) still matches: at most three line breaks,
        #   after "Le", inside the gap and before "a écrit", never a blank line.
        #   The negative lookahead stays on one line (.), as upstream has it.
        #   See email_crisp_fr_multiline.txt / email_fr_gmail_wrapped.txt for example data
        # ^...$ anchoring retained from upstream's PR #25 (line-anchoring fix).
        'wrote_header': r'^(?!Le.*Le\s.+?a \u00e9crit[a-zA-Z0-9.:;<>()&@ -]*:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Le\s' + WRAPPED_GAP + r'\s?a \u00e9crit[a-zA-Z0-9.:;<>()&@ -]*:)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:De |Envoy\u00e9 |\u00C0 |Objet |  |Cc ):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'signatures': [
            'cordialement',
            'salutations',
            r'bonne r[\u00e9e]ception',
            r'bonne journ[\u00e9e]e',
            # "bonne soirée" / "Bien à vous" — ported from
            # crisp-oss/email-reply-parser; no fixture in the upstream repo
            # currently exercises these lines.
            r'bonne soir[\u00e9e]e',
            r'Bien \u00e0 vous',
        ],
        'sent_from': r'Envoy\u00e9 \u00e0 partir de|Envoy\u00e9 de mon|Envoy\u00e9 depuis|T\u00e9l\u00e9charger Outlook pour',
    },
    'it': {
        # Accept both "Il <date> ha scritto:" and "In data <date> ha scritto:"
        # (the latter is the phrasing used by some Italian Outlook locales).
        'wrote_header': r'^(?!(?:Il|In data)[.\s]*(?:Il|In data)\s(' + WRAPPED_GAP + r')\sha scritto:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'(?:Il|In data)\s' + WRAPPED_GAP + r'\s?ha scritto:)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Da|Inviato|A|Oggetto|Data|Cc):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'signatures': [
            'Cordiali saluti',
        ],
        'sent_from': 'Inviato da',
    },
    'ja': {
        'wrote_header': r'^(?!.*\d{4}年\d{1,2}月\d{1,2}日\(.\) \d{1,2}:\d{2}.+? <.+?>:.*\d{4}年\d{1,2}月\d{1,2}日\(.\) \d{1,2}:\d{2}.+? <.+?>:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'\d{4}年\d{1,2}月\d{1,2}日\(.\) \d{1,2}:\d{2}.+? <.+?>):$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:From|Sent|To|Subject|Date|Cc):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [],
        'signatures': [],
        'sent_from': '',
    },
    'ko': {
        'wrote_header': r'^(?!.*\d{4}년 \d{1,2}월 \d{1,2}일.*?님이 작성하였습니다:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'\d{4}년 \d{1,2}월 \d{1,2}일 .*님이 작성하였습니다:)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:보낸\s?사람|보낸\s?날짜|받는\s?사람|제목|참조):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            '주의:',
            '면책 조항:',
            '비밀정보:',
        ],
        'signatures': [
            '감사합니다,',
            '안부 전합니다,',
            '좋은 하루 되세요,',
            '고맙습니다,',
            '감사합니다.',
        ],
        'sent_from': r'내 .*에서 보냄',
    },
    'nl': {
        'wrote_header': r'^(?!Op[.\s]*Op\s(' + WRAPPED_GAP + r')\sschreef:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Op\s' + WRAPPED_GAP + r'\s?schreef:)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Van|Verzonden|Aan|Onderwerp|Datum|Cc):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            'Disclaimer:',
            'Waarschuwing:',
        ],
        'signatures': [
            'Met vriendelijke groet',
            'Hartelijke groeten',
            'Bedankt,',
            'Dank u,',
        ],
        'sent_from': 'Verzonden vanaf mijn',
    },
    'pl': {
        'wrote_header': r'^(?!Dnia[.\s]*Dnia\s(' + WRAPPED_GAP + r')\s(?:nadesłał|napisał\(a\)):)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Dnia\s' + WRAPPED_GAP + r'\s?(?:nadesłał|napisał\(a\)):)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Od|Wysłano|Do|Temat|Data|DW):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            'Uwaga:'
        ],
        'signatures': [
            'Z poważaniem',
            'Z powazaniem',
            'Pozdrawiam',
            'W przypadku niejasności, proszę o kontakt.'
        ],
        'sent_from': 'Wysłano z'
    },
    'pt': {
        # Portuguese: "Em <date>, <name> <email> escreveu:"; the header can wrap within the
        #   bounded gap shared with the other languages (at most three line breaks, never
        #   a blank line).
        # Example: "Em 10 de julho de 2017 às 16:32:35, John Doe (a@b.com) escreveu:"
        'wrote_header': r'^(?!Em[.\s]*Em\s(' + WRAPPED_GAP + r')\sescreveu:)('
                        + QUOTED_MATCH_INCLUDE
                        + r'Em\s' + WRAPPED_GAP + r'\s?escreveu:)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:De|Enviado|Para|Assunto|Data|CC):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [],
        'signatures': [
            'Atenciosamente',
            'Cumprimentos',
            r'Abra\u00e7os',
            'Obrigado',
        ],
        'sent_from': 'Enviado do meu',
    },
    'sv': {
        'wrote_header': r"^(?!Den[.\s]*Den\s(" + WRAPPED_GAP + r")\skrev:)("
                        + QUOTED_MATCH_INCLUDE
                        + r"(?:Den|[Mm]ån|[Tt]is|[Oo]ns|[Tt]or|[Ff]re|[Ll]ör|[Ss]ön|(?:[0-9]+\s+(?:jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec)))[^\n]*skrev\s" + WRAPPED_GAP + r":)$",
        'disclaimers': [
            'Varning:',
            'Observera:',
        ],
        'signatures': [
            'Med vänliga hälsningar',
            'Vänliga hälsningar',
            'Hälsningar',
            'Bästa hälsningar',
            'Mvh',
            r'/\w+',  # To match /John, /Anna, etc.
        ],
        'sent_from': 'Skickat från min',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:Från|Skickat|Till|Ämne|Datum|Kopia):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
    },
    'zh': {
        'wrote_header': r'^(?!.*\d{4}年\d{1,2}月\d{1,2}日.*?写道：)('
                        + QUOTED_MATCH_INCLUDE
                        + r'\d{4}年\d{1,2}月\d{1,2}日.*?写道：)$',
        'from_header': r'((?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE
                       + r')[* ]*(?:发件人|发送时间|收件人|主题|抄送|组织):[ *]*(?:\s{,2}).*){2,}(?:\n.*){,1})',
        'disclaimers': [
            '免责声明：',
            '注意：',
            '重要信息：',
        ],
        'signatures': [
            '此致，',
            '敬礼，',
            '谢谢，',
            '谢谢您的关注，',
            '祝好，',
        ],
        'sent_from': r'从我的.*发送',
    },
    'david': {
        # Custom Software Headers – also kind of like a language, right?
        'from_header': r'((?:^ *' + QUOTED_MATCH_INCLUDE + r'\[?Original Message processed by david.+?$\n{,4})'
                       + r'(?:.*\n?){,2}'  # david's non-subject line + date wildcard identification
                       + r'(?:(?:^|\n|\n'
                       + QUOTED_MATCH_INCLUDE + r')[* ]*(?:Von|An|Cc)(?:\s{,2}).*){2,})'
    },
}
