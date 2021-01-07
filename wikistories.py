import pywikibot
import re
import pandas as pd

class Article:
    site = pywikibot.Site('en', 'wikipedia')

    def __init__(self, title):
        self.title = title
        self.revs_fetched = False
        self.page = pywikibot.Page(self.site, self.title)
    
    def __str__(self):
        if self.revs_fetched is False:
            info = "Article('{title}')".format(
                title=self.title
            )
        else:
            info = "Article('{title}', {numrev} revisions)".format(
                title=self.title,
                numrev=self.num_rev
            )
        return info

    def __repr__(self):
        return str(self)

    def get_revisions(self, spec, starttime=None, endtime=None):
        if spec is 'all':
            total = None
        elif isinstance(spec, int):
            total = spec
        else:
            raise TypeError("Revision specification must be an integer or 'all'")
        # the following may break for articles with very long histories
        self.rev_data = list(self.page.revisions(
            total=total,
            content=False,
            starttime=starttime,
            endtime=endtime,
            reverse=True
        ))
        self.num_rev = len(list(self.rev_data))
        self.revs_fetched = True
        print('Successfully fetched data for {num_rev} revisions.'.format(
            num_rev=self.num_rev
        ))

    def ids(self):
        if not self.revs_fetched:
            raise Exception('No revision data fetched!')
        else:
            return [ rev.revid for rev in self.rev_data ]

    def sizes(self):
        if not self.revs_fetched:
            raise Exception('No revision data fetched!')
        else:
            return [ rev.size for rev in self.rev_data ]            
    
    def timestamps(self, date_format='isostring'):
        if not self.revs_fetched:
            raise Exception('No revision data fetched!')
        else:
            if date_format is 'wiki':
                return [ rev.timestamp.totimestampformat() for rev in self.rev_data ]
            elif date_format is 'isostring':
                return [ rev.timestamp.isoformat() for rev in self.rev_data ]
            elif date_format is 'unix':
                return [ rev.timestamp.timestamp() for rev in self.rev_data ]
            else:
                raise Exception('Unknown date format!')

    def to_data_frame(self, date_format='isostring'):
        df = pd.DataFrame()
        df['ids'] = self.ids()
        df['sizes'] = self.sizes()
        df['timestamps'] = self.timestamps()
        return df
    
    def linked(self, dist=1, return_strings=False):
        if dist > 2:
            raise Exception('Linked articles only supported up to 2nd neighbour!')
        linked = re.findall('\[\[([^\]\#\|]+)[^\[]*\]\]', self.page.text)
        linked = list(set(linked))
        if dist is 1:
            if return_strings:
                return linked
            else:
                return [Article(name) for name in linked]
        elif dist is 2:
            linked2nd = []
            for name in linked:
                linked2nd.extend(Article(name).linked(return_strings=True))
            linked2nd = list(set(linked2nd))
            if return_strings:
                return linked2nd
            else:
                return [Article(name) for name in linked2nd]