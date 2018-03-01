import json
import glob
import optparse

usage = 'Usage: %prog [ --all --cont ]'
parser = optparse.OptionParser(usage=usage)
parser.add_option('-f', '--filepath', action='store', default=None,
                  help='Path to files, e.g. parguay/sample')
parser.add_option('-V', '--verbose', action='store_true', default=False,
                  help='Print verbose output')
(options, args) = parser.parse_args()
if not options.filepath:
    parser.error('You must supply a filepath, using the -f argument')

files = glob.glob('%s*' % options.filepath)

with open('output.jsonl', 'w') as writefile:
    for i, filename in enumerate(files):
        with open(filename,"r") as data_all:
            data = json.loads(data_all.read())
            for grant in data['grants']:
                json.dump(grant, writefile)
                writefile.write('\n')
                print(".",end='')