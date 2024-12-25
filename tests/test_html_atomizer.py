from lib.html_atomizer import HTMLPage
import json
import datetime
import parsel

TEST_HTML_TEXT = r'''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Example Page</title>
</head>
<body>

<ul>
  <!-- First entry -->
  <li class="ipsDataItem">
    <h4 class="ipsDataItem_title">
      <span class="ipsContained">
        <a href="https://example.com/topic/12345">
          Placeholder Title 1
        </a>
      </span>
    </h4>

    <div class="ipsDataItem_main">
      <p class="ipsType_light">
        <!-- Author name + profile link -->
        <a href="https://example.com/profile/user1" title="profile of user1">
          Placeholder Author 1
        </a>
      </p>
      <!-- Summary text -->
      <div class="ipsType_medium">
        This is a short summary of the topic. Lorem ipsum dolor sit amet.
      </div>
    </div>

    <div class="ipsDataItem_generic">
      <!-- Date/time -->
      <p class="ipsType_medium">
        <time datetime="2024-01-02T14:00:00Z"></time>
      </p>
      <!-- The image is extracted from the inline style via substring XPath -->
      <a title="More information"
         style='background-image: url( "https://protected.example.com/images/placeholder1.png" );'>
      </a>
    </div>
  </li>

  <!-- Second entry -->
  <li class="ipsDataItem">
    <h4 class="ipsDataItem_title">
      <span class="ipsContained">
        <a href="https://example.com/topic/54321">
          Placeholder Title 2
        </a>
      </span>
    </h4>

    <div class="ipsDataItem_main">
      <p class="ipsType_light">
        <a href="https://example.com/profile/user2" title="profile of user2">
          Placeholder Author 2
        </a>
      </p>
      <div class="ipsType_medium">
        Another summary text snippet goes here. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
      </div>
    </div>

    <div class="ipsDataItem_generic">
      <p class="ipsType_medium">
        <time datetime="2024-05-10T09:30:00Z"></time>
      </p>
      <a title="More information"
         style='background-image: url( "https://protected.example.com/images/placeholder2.png" );'>
      </a>
    </div>
  </li>
</ul>

</body>
</html>
    
'''

TEST_FEED_CONFIG = r"""
{
  "feed_type": "html",
  "handling": "cloudflare",
  "image_proxy_domains": ["protected.example.com"],
  "uri": ["https://www.example.com/files/category/1-test/", "https://www.example.com/files/category/2-test2/"],
  "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15",
  "entries": "//li[has-class('ipsDataItem')]",
  "title": ".//h4[has-class('ipsDataItem_title')]/span[has-class('ipsContained')]/a/text()",
  "link": ".//h4[has-class('ipsDataItem_title')]/span[has-class('ipsContained')]/a/@href",
  "author": "./div[has-class('ipsDataItem_main')]/p[has-class('ipsType_light')]/a/text()",
  "author_uri": "./div[has-class('ipsDataItem_main')]/p[has-class('ipsType_light')]/a[contains(@title, 'profile')]/@href",
  "date": "./div[has-class('ipsDataItem_generic')]/p[has-class('ipsType_medium')]//time/@datetime",
  "summary": "./div[has-class('ipsDataItem_main')]/div[has-class('ipsType_medium')]//text()",
  "image": "substring-before(substring-after(./div[has-class('ipsDataItem_generic')]/a[contains(@title, 'More information')]/@style, 'url( \"'), '\" )')"
}

"""

def test_parse_entries_from_html():
    page = HTMLPage(json.loads(TEST_FEED_CONFIG))
    entries = page.parse_entries_from_html(TEST_HTML_TEXT)
    print(entries[0])
    assert len(entries) == 2
    assert entries[0].link == "https://example.com/topic/54321"
    assert entries[0].author == "Placeholder Author 2"
    assert entries[0].author_uri == "https://example.com/profile/user2"
    assert entries[0].title == "Placeholder Title 2"
    assert entries[0].date == datetime.datetime(2024, 5, 10, 9, 30, tzinfo=datetime.timezone.utc)
    assert entries[0].summary_html == "Another summary text snippet goes here. Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    assert entries[0].image == ["https://protected.example.com/images/placeholder2.png"]

def test_atom_output():
    page = HTMLPage(json.loads(TEST_FEED_CONFIG))
    entries = page.parse_entries_from_html(TEST_HTML_TEXT)
    page.entries = entries
    feed = page.to_feed("https://example.com/category/12345", image_proxy_uri="https://myapp.example.org/my_proxy_script")
    selector = parsel.Selector(text=feed.decode('utf-8'), type='xml')
    selector.remove_namespaces() # enable easier XPath selection
    # read Atom feed and verify entry
    assert selector.xpath('//feed/title/text()').get() == "Example Page"
    assert selector.xpath('//feed/entry/title/text()').get() == "Placeholder Title 2"
    assert selector.xpath('//feed/entry/author/name/text()').get() == "Placeholder Author 2"
    assert selector.xpath('//feed/entry/author/uri/text()').get() == "https://example.com/profile/user2"
    assert selector.xpath('//feed/entry/content/text()').get() == "<div class='post_image'><img src='https://myapp.example.org/my_proxy_script?uri=https://protected.example.com/images/placeholder2.png' /></div>\n<div class='post_text'>Another summary text snippet goes here. Lorem ipsum dolor sit amet, consectetur adipiscing elit.</div>"
    assert selector.xpath('//feed/entry/link/@href').get() == "https://example.com/topic/54321"

