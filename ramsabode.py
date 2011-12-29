import urllib2
import calendar

PAGE_URL = 'http://ramsabode.wordpress.com/concerts-in-chennai'
months = calendar.month_name[1:]

class RamIterator:
    def __init__(self):
        fp = urllib2.urlopen(PAGE_URL)
        self.skip_data(fp)
        self.myiter = iter(fp)

    def __iter__(self):
        return self

    def next(self):
        #import pdb
        #pdb.set_trace()
        while True:
            line = self.myiter.next()
            line = line.strip()
	    if line.find('text-decoration:underline') != -1:
                line = self.remove_tags(line)
                line = line.strip()
                if not line:
                    # month being underlined
                    continue
                line = line.split()
                if line[1] not in months:
                    raise StopIteration
                self.year = int(line[2])
                self.day = line[0]
                assert(self.day.endswith('st') or self.day.endswith('nd') or \
                       self.day.endswith('rd') or self.day.endswith('th'))
                self.day = int(self.day[:-2])
                self.month = months.index(line[1]) + 1
            else:
                if line.find('@') != -1:
                    line = line.split('@')
                    loc = line[1].strip()
                    line = self.remove_tags(line[0])
                    line = line.replace('&#8211;', '-')
                    line = line.replace('\xe2\x80\x93', '-')
                    line = line.replace('\xc2\xa0', '')
                    line = line.split('-', 1)
                    start_time = line[0].split()
                    if len(start_time) not in [2,5]:
                        continue
                    who = line[-1].strip()
                    return self.year, self.month, self.day, start_time, who, loc


    def skip_data(self, fp):
        for line in fp:
            line = line.strip()
            line = self.remove_tags(line)
            line = line.split()
            if len(line) == 2 and line[0].capitalize() in months:
                return True
        return False

    def remove_tags(self, line):
        while 1:
            pos = line.find('<')
            if pos == -1:
                break
            pos1 = line.find('>', pos)
            if pos1 == -1:
                break
            line = line[:pos] + line[pos1+1:]
        return line
 

if __name__ == "__main__":
    r1 = RamIterator()
    for x in r1:
        print x
