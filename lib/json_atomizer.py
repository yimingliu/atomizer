from lib.atomizer import Entry, Page
from parsel import Selector
import dateutil.parser, dateutil.tz
import datetime

class JSONPage(Page):

    def parse_entries_from_json(self, json_text):
        parsed_entries = []
        selector = Selector(text=json_text, type='json')
        entries = selector.jmespath(self.config['entries'])
        self.title = self.get_json_value(selector, 'feed_title', default="")
        self.image = self.get_json_value(selector, 'feed_image')
        self.itunes_category = self.get_json_value(selector, 'itunes_category')
        self.itunes_explicit = self.get_json_value(selector, 'itunes_explicit', default=False)
        if entries:
            for entry in entries:
                link = self.get_json_value(entry, 'link')
                if not link:
                    continue
                entry_date = self.get_json_value(entry, 'date')
                default_date = datetime.datetime.combine(datetime.datetime.now(),
                                                datetime.time(0, tzinfo=dateutil.tz.tzutc()))
                item = Entry(link=link, title=self.get_json_value(entry, 'title', default=link),
                             date=dateutil.parser.parse(entry_date,
                                                        default=default_date) if entry_date else default_date,
                             author=self.get_json_value(entry, 'author', default=""),
                             author_uri=self.get_json_value(entry, 'author_uri', default=""),
                             summary=[self.get_json_value(entry, 'summary', default="")])
                enclosure_path = self.get_json_value(entry, 'enclosures')
                if enclosure_path:
                    enclosure = {
                        "href": enclosure_path,
                        "type": "audio/mpeg" if enclosure_path.endswith(".mp3") else None
                    }
                    item.enclosures.append(enclosure)
                parsed_entries.append(item)
        if parsed_entries:
            parsed_entries.sort(key=lambda x: x.date, reverse=True)
        return parsed_entries

    def parse_entries_from_response(self, response):
        return self.parse_entries_from_json(response.text)

    def get_json_value(self, selector, key, default=None):
        path = self.config.get(key)
        if path:
            return selector.jmespath(path).get()
        return self.config.get(f"{key}_default", default)
