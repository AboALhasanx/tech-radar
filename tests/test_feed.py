from radar.feed import parse_date, parse_feed, strip_html

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>t</title>
<item>
  <title>Tweet text here - X</title>
  <link>https://news.google.com/rss/articles/abc</link>
  <pubDate>Wed, 29 Oct 2026 07:00:00 GMT</pubDate>
  <description>&lt;p&gt;hello &amp;amp; bye&lt;/p&gt;</description>
</item>
</channel></rss>"""

ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Post title</title>
    <link href="https://reddit.com/r/x/1"/>
    <updated>2026-10-28T10:00:00Z</updated>
    <summary>&lt;b&gt;body&lt;/b&gt;</summary>
  </entry>
</feed>"""


def test_parse_rss():
    items = parse_feed(RSS)
    assert len(items) == 1
    assert items[0]["title"] == "Tweet text here - X"
    assert items[0]["link"].startswith("https://news.google.com")
    assert items[0]["published"].year == 2026


def test_parse_atom():
    items = parse_feed(ATOM)
    assert len(items) == 1
    assert items[0]["link"] == "https://reddit.com/r/x/1"
    assert items[0]["summary"] == "body"


def test_bad_xml_returns_empty():
    assert parse_feed("<not xml") == []


def test_strip_html_unescapes():
    assert strip_html("<p>a &amp; b</p>") == "a & b"


def test_parse_date_variants():
    assert parse_date("Wed, 29 Oct 2026 07:00:00 GMT").year == 2026
    assert parse_date("2026-10-28T10:00:00Z").hour == 10
    assert parse_date("nonsense") is None
    assert parse_date(None) is None
