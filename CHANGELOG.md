# Changelog

Changes in the Lucidity-Factory fork since upstream 1.36 (`fc44bc8`). `version.py` still reads 1.36; pin the fork by commit.

## Unreleased (fork)

### Breaking

- **No new text gives an empty latest reply.** When the plain text starts with a quote header (an attribution, a `From:` or `Od:` block, or a forward separator), `latest_reply` and `parse_reply()` now return `''` and `replies[0]` is an empty reply; the quoted message follows in the next replies. Upstream returned the header and the quote as if they were the reply. A forward gets no special treatment: one with nothing written above its separator also gives `''`. (`d0ae8fe`. An earlier version kept the text after a separator when no header block followed it; that was removed, since on the one real case the text it kept was forwarded content.)
- **Separators become their own reply.** Gmail and Zoho "Forwarded message" separators and Outlook's underscore line before `From:` are now headers, so such messages have one more entry in `replies`, holding only the separator. `latest_reply` no longer ends with the separator line. (`01899b7`, `8123a81`)

### Added

- Portuguese (`pt`) and Finnish (`fi`). (`371911d`, `6d876de`, `ce932ff`)
- Patterns ported from crisp-oss/email-reply-parser: DE/FR/DA "Original Message" separators, wrapped French `Le ... a écrit :`, Italian `In data ... ha scritto:`, French mobile sent-from lines, more signature phrases. Attribution in `NOTICE`. (`29e12cb` to `a838c02`)
- Client formats seen in real mail: Mail.ru / myMail headers, header blocks with a blank line between fields, Gmail and Zoho forward separators, the Zoho / Yahoo `---- On ... wrote ----` header. (`01899b7`, `7944e14`)

### Fixed

- Quote headers are no longer slow on long lines: the shared gap between start word and verb is linear (a 12 KB line took about 2 s). (`02be4cb`)
- Headers are located where they matched, not by searching the text for the header string. (`894b9c7`)
- Polish header blocks need two fields, like every other language. (`07db9e3`)
- A hyphen list in the new text is no longer taken for a "-John" signature. (`9293629`)
- Every underscore separator after a blank line is normalised, not only the first 8. (`e741a87`)
