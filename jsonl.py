import json
import glob
import optparse
import requests

from jsonschema import Draft3Validator

schema = json.loads(requests.get('https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-schema.json').text)

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

def remove_extra_fields(data, schema, IS_VERBOSE):
    '''
    Delete extra fields reported by jsonschema.
    This is pretty inelegant, and jsonschema is a bit unpredictable
    about what it reports, see e.g. https://goo.gl/yCNGMw
    I think personally I'd ditch this code and just delete
    fields manually, given that (a) it's actually helpful to examine
    what publishers have supplied - often they just misname fields,
    which can usefully be renamed rather than deleted (b) almost
    always, other manual tweaks are required to get the data into shape,
    so it's never going to be a fully automated process anyway
    (c) there aren't many publishers, so it's not much of an overhead.
    '''
    has_extra_fields = False
    v = Draft3Validator(schema)
    errors = sorted(v.iter_errors(data), key=str)
    for error in errors:
        temp = data
        error_path = error.absolute_schema_path

        # Ignore all errors apart from extra properties.
        if error_path[-1] == 'additionalProperties':
            has_extra_fields = True
            # Hacky way to get property names, but seems to be
            # the best offered by jsonschema.
            unwanted_properties = re.findall(r"'(\w+)'", error.message)
            path_expression = []
            for i, e in enumerate(error_path):
                if e == 'additionalProperties':
                    continue
                if e == 'properties':
                    i += 1
                    path_expression.append(error_path[i])
            if IS_VERBOSE:
                print('\nJSONSchema raw error path: %s' % error_path)
                print('Processed error path: %s' % path_expression)
                print('Unwanted properties: %s' % unwanted_properties)

            # We now have details of the unwanted properties: remove them
            # from the data object.
            # First retrieve the relevant part of the data. We can't predict
            # whether this will be a dict or a list.
            for p in path_expression:
                if p in temp:
                    temp = temp[p]
                elif isinstance(temp, list):
                    temp_x = []
                    for t in temp:
                        if isinstance(t, dict) and p in t:
                            temp_x.append(t[p])
                    if temp_x:
                        temp = temp_x
            # Now iterate over the relevant part of the data, and remove
            # the unwanted property.
            if isinstance(temp, list):
                # Flatten lists of lists.
                if any(isinstance(el, list) for el in temp):
                    flat_list = [item for sublist in temp for item in sublist]
                    temp = flat_list
                for d in temp:
                    for unwanted_property in unwanted_properties:
                        if unwanted_property in d:
                            del d[unwanted_property]
                        else:
                            t = None
                            # Use the last property in the path if required.
                            if path_expression[-1] in d:
                                t = d[path_expression[-1]]
                            elif len(path_expression) > 1 and path_expression[-2] in d and path_expression[-1] in \
                                    d[path_expression[-2]]:
                                t = d[path_expression[-2]][path_expression[-1]]
                            if isinstance(t, list):
                                for s in t:
                                    if unwanted_property in s:
                                        del s[unwanted_property]
                            elif t:
                                if unwanted_property in t:
                                    del t[unwanted_property]
            else:
                for unwanted_property in unwanted_properties:
                    if unwanted_property in temp:
                        del temp[unwanted_property]

    return data, has_extra_fields

with open('output.jsonl', 'w') as writefile:
    for i, filename in enumerate(files):
        with open(filename,"r") as data_all:
            data = json.loads(data_all.read())
            for grant in data['grants']:
                has_extra_fields = True
                while has_extra_fields:
                    grant, has_extra_fields = remove_extra_fields(
                        grant, schema, 'true')
                json.dump(grant, writefile)
                writefile.write('\n')
                print(".",end='')