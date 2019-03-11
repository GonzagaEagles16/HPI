from datetime import datetime
import json
from pathlib import Path
import pytz
from typing import NamedTuple, Optional, List, Dict
from collections import OrderedDict

from kython import group_by_key

BDIR = Path('/L/backups/instapaper/')

Bid = str
Hid = str

class Highlight(NamedTuple):
    dt: datetime
    uid: Hid
    bid: Bid
    text: str
    note: Optional[str]
    url: str
    title: str

    @property
    def instapaper_link(self) -> str:
        return f'https://www.instapaper.com/read/{self.bid}/{self.uid}'


class Bookmark(NamedTuple):
    bid: Bid
    dt: datetime
    url: str
    title: str

    @property
    def instapaper_link(self) -> str:
        return f'https://www.instapaper.com/read/{self.bid}'


class Page(NamedTuple):
    bookmark: Bookmark
    highlights: List[Highlight]

def get_files():
    return sorted(f for f in BDIR.iterdir() if f.suffix == '.json')

def dkey(x):
    return lambda d: d[x]


def make_dt(time) -> datetime:
    return pytz.utc.localize(datetime.utcfromtimestamp(time))


def get_stuff(all=True):
    all_bks: Dict[Bid, Bookmark] = OrderedDict()
    all_hls: Dict[Hid, Highlight] = OrderedDict()
    # TODO can restore url by bookmark id
    for f in get_files():
        with f.open('r') as fo:
            j = json.load(fo)
        for b in sorted(j['bookmarks'], key=dkey('time')):
            bid = str(b['bookmark_id'])
            prev = all_bks.get(bid, None)
            # assert prev is None or prev == b, '%s vs %s' % (prev, b)
            # TODO shit, ok progress can change apparently
            all_bks[bid] = Bookmark(
                bid=bid,
                dt=make_dt(b['time']),
                url=b['url'],
                title=b['title'],
            )
        hls = j['highlights']
        for h in sorted(hls, key=dkey('time')):
            hid = h['highlight_id']
            bid = str(h['bookmark_id'])
            # TODO just reference to bookmark in hightlight?
            bk = all_bks[bid]
            h = Highlight(
                uid=hid,
                bid=bk.bid,
                dt=make_dt(h['time']),
                text=h['text'],
                note=h['note'],
                url=bk.url,
                title=bk.title,
            )
            prev = all_hls.get(hid, None)
            assert prev is None or prev == h
            all_hls[hid] = h

    return all_bks, all_hls

def iter_highlights():
    return iter(get_stuff()[1])


def get_highlights():
    return list(iter_highlights())


def get_todos():
    def is_todo(h):
        return h.note is not None and h.note.lstrip().lower().startswith('todo')
    return list(filter(is_todo, get_highlights()))


def get_pages() -> List[Page]:
    bms, hls = get_stuff()
    groups = group_by_key(hls.values(), key=lambda h: h.bid)
    pages = []
    # TODO how to make sure there are no dangling bookmarks?
    for bid, bm in bms.items():
        pages.append(Page(
            bookmark=bm,
            highlights=sorted(groups.get(bid, []), key=lambda b: b.dt),
        ))
    return pages


def main():
    for h in get_todos():
        print(h)

if __name__ == '__main__':
    main()
