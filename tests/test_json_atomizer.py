from lib.json_atomizer import JSONPage
import json
import datetime
import parsel

TEST_JSON_TEXT = """
    [
      {
        "id": "1",
        "user": "12345",
        "service": "test_service",
        "title": "Test Title 1",
        "content": "<p>Sample content for test case 1.</p>",
        "added": "2024-01-01T00:00:00.000000",
        "published": "2024-01-02T00:00:00",
        "edited": "2024-01-02T00:00:00",
        "file": {
          "name": "test_file_1.mp3",
          "path": "/test/path/to/test_file_1.mp3"
        },
        "attachments": [
          {
            "name": "attachment1.mp3",
            "path": "/test/path/to/attachment1.mp3"
          },
          {
            "name": "attachment2.png",
            "path": "/test/path/to/attachment2.png"
          },
          {
            "name": "attachment3.png",
            "path": "/test/path/to/attachment3.png"
          }
        ]
      },
      {
        "id": "2",
        "user": "67890",
        "service": "test_service",
        "title": "Test Title 2",
        "content": "<p>Sample content for test case 2.</p>",
        "added": "2024-01-03T00:00:00.000000",
        "published": "2024-01-04T00:00:00",
        "edited": null,
        "file": {
          "name": "test_file_2.mp3",
          "path": "/test/path/to/test_file_2.mp3"
        },
        "attachments": [
          {
            "name": "attachment4.mp3",
            "path": "/test/path/to/attachment4.mp3"
          },
          {
            "name": "attachment5.png",
            "path": "/test/path/to/attachment5.png"
          },
          {
            "name": "attachment6.png",
            "path": "/test/path/to/attachment6.png"
          }
        ]
      }
    ]

    """
TEST_FEED_CONFIG = """
{
  "feed_type": "json",
  "output_type": "podcast",
  "feed_title_default": "Test Feed",
  "feed_image_default": "https://example.com/?foo=bar.png",
  "itunes_category_default": "Technology",
  "itunes_explicit_default": "no",
  "uri": "https://example.com/podcast/12345",
  "entries": "[? file.path != null && contains(file.path, '.mp3')]",
  "title": "title",
  "link": "join('', ['https://example.com/podcast/', user, '/episode/', id])",
  "author_default": "John Doe",
  "author_uri": "join('', ['https://example.com/podcast/', user])",
  "date": "edited || published || added",
  "summary": "content",
  "enclosures": "join('', ['https://example.com', file.path || ''])",
  "offset_param": "o",
  "per_page": 50
}
"""


def test_parse_entries_from_json():
    page = JSONPage(json.loads(TEST_FEED_CONFIG))
    entries = page.parse_entries_from_json(TEST_JSON_TEXT)
    assert len(entries) == 2
    assert entries[1].link == "https://example.com/podcast/12345/episode/1"
    assert entries[1].author == "John Doe"
    assert entries[1].author_uri == "https://example.com/podcast/12345"
    assert entries[1].title == "Test Title 1"
    assert entries[1].date == datetime.datetime(2024, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
    assert entries[1].summary_html == "<p>Sample content for test case 1.</p>"
    assert len(entries[1].enclosures) == 1
    assert entries[1].enclosures[0]['href'] == "https://example.com/test/path/to/test_file_1.mp3"
    assert entries[1].enclosures[0]['type'] == "audio/mpeg"


def test_podcast_output():
    page = JSONPage(json.loads(TEST_FEED_CONFIG))
    entries = page.parse_entries_from_json(TEST_JSON_TEXT)
    page.entries = entries
    feed = page.to_feed("https://example.com/podcast/12345")
    selector = parsel.Selector(text=feed.decode('utf-8'), type='xml', namespaces={'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'})
    assert selector.xpath('//rss/channel/title/text()').get() == "Test Feed"
    assert selector.xpath('//rss/channel/image/url/text()').get() == "https://example.com/?foo=bar.png"
    assert selector.xpath('//rss/channel/itunes:category/@text').get() == "Technology"
    assert selector.xpath('//rss/channel/itunes:explicit/text()').get() == "no"
    assert selector.xpath('//rss/channel/itunes:author/text()').get() == "John Doe"
    # item level fields
    assert selector.xpath('//rss/channel/item/pubDate/text()').get() == "Thu, 04 Jan 2024 00:00:00 +0000"
    assert selector.xpath('//rss/channel/item/title/text()').get() == "Test Title 2"






