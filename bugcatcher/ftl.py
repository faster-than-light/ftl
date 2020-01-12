# -*- coding: utf-8 -*-

# !/usr/bin/env python3

import argparse
from git import Repo
import json
import shutil, os
import sys
import textwrap
import re
import requests
import hashlib
import base64
from time import sleep
from colorama import Fore, Back, Style
import inspect

# XXX FIXME REMOVE THESE
# from SID import SID
# from TestRun import TestRun
# from TestSuite import TestSuite
# from TestRunResult import TestRunResult
# from Login import current_login

args = None
default_extensions = []
max_retries_get_test_result = 5

path_ignore_pieces = [re.compile('/__'),
                      re.compile('^__'),
                      re.compile('/venv/'),
                      re.compile('^venv/'),
                      re.compile('^\.git'),
                      re.compile('/\.git'),
                      re.compile('^node_modules/'),
                      re.compile('/node_modules/')]

exit_error = {'command_unspecified': -2,
              'unknown_command': -3,
              'unable_to_determine_project': -4,
              'unable_to_determine_side': -5,
              'textually_invalid_sid': -6,
              'invalid_sid': -7,
              'no_json_returned_on_rest_call': -8,
              'rest_call_err': -9,
              'rest_call_no_response': -10,
              'required_arg_not_found': -11
              }


def abort(err, errstr):
    print(errstr, file=sys.stderr)
    exit(exit_error[err])


def line_num():
    # Returns the current line number in our program
    return 'Line ' + str(inspect.currentframe().f_back.f_lineno)


# Strip off leading ../s from paths
def strip_relative_path(dir_name):
    pieces = os.path.normpath(dir_name).split(os.path.sep)

    true_path_start = None

    for x in range(0, len(pieces)):
        if pieces[x] != '..' and pieces[x] != '.':
            true_path_start = x
        else:
            true_path_start = None

    exit(0)

    return '/'.join(pieces[true_path_start:])


def sha256_file(fn):
    sha256 = hashlib.sha256()

    # We don't just slurp it for memory reasons on large files.
    with open(fn, 'rb') as inf:
        # Read 64-KB chunks
        while True:
            data = inf.read(65536)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


def print_line(line_num, to_print, label='', label_color='YELLOW', outline=False):
    """
    Print with line numbers

    Print something with the line number and optionally add a frame border

    Parameters:
    line_num (int): Line number where print_line is called
    to_print (*): Object, String, Number, etc to be printed
    label (string): Label added as prefix
    label_color (string): Color override for Label
    outline (bool): Adds linebreaks and borders around `to_print`

    """

    if 'FTL_DEV' in os.environ:

        # Use a specified label_color
        label_color = label_color.upper()
        if label_color == 'BLACK': label_color = Fore.BLACK
        if label_color == 'RED': label_color = Fore.RED
        if label_color == 'GREEN': label_color = Fore.GREEN
        if label_color == 'YELLOW': label_color = Fore.YELLOW
        if label_color == 'BLUE': label_color = Fore.BLUE
        if label_color == 'MAGENTA': label_color = Fore.MAGENTA
        if label_color == 'CYAN': label_color = Fore.CYAN
        if label_color == 'WHITE': label_color = Fore.WHITE
        if label_color == 'RESET': label_color = Fore.RESET
        label = str(label_color + label + Fore.RESET)

        divider = Style.DIM + "=*" * 45 + Style.RESET_ALL

        if outline:
            print('\n' + divider)

        print(
            "%s %s %s: %s" % (
                str(Style.DIM + '>' + Style.RESET_ALL),
                str(Fore.YELLOW + line_num + Fore.RESET),
                label,
                to_print
            )
        )

        if outline:
            print(divider + '\n')


def add_to_push_list(file_list, base_path_index, dir_name, extensions, to_submit):
    """
    Add a file to the `to_submit` push list used in `process_dir()`

    :param <list> file_list: List of files to be pushed
    :param <int> base_path_index: Index of the base path
    :param <str> dir_name: Directory name
    :param <list> extensions: File extensions we want to push
    :param <dict> to_submit: Dictionary of files to be pushed. (appended in this function)
    :return: <dict> Dictionary of files to be pushed
    """
    for filename in file_list:
        if not filename.startswith("./"):
            tmp_fn, extension = os.path.splitext(filename)

            if not extensions or extension.lower() in extensions:
                raw_fn = "%s/%s" % (dir_name, filename)
                pieces = os.path.normpath(raw_fn).split(os.path.sep)
                fn = (os.path.sep).join(pieces[base_path_index:])

                if not len(fn):
                    # Redefine the filenames for files in the basepath dir
                    raw_fn = fn = pieces[0]

                if raw_fn.startswith("./"):
                    # Clean it up for syncing with the backend
                    raw_fn = raw_fn[2:]

                to_submit[raw_fn] = {'raw_fn': raw_fn,
                                     'sha256': sha256_file(raw_fn),
                                     'fn': fn}

    return to_submit


def process_dir(to_submit, fn, extensions):
    # First off, we need to know the base path, so that we can
    # strip off extraneous parts of the path before we look for
    # things we want to ignore.
    pieces = os.path.normpath(fn).split(os.path.sep)
    base_path_index = len(pieces)

    is_directory = None

    for dir_name, sub_dir_list, file_list in os.walk(fn, topdown=True):
        # Clean up the dir_name for evaluation later
        eval_dir_name = dir_name
        if dir_name.startswith('.' + os.path.sep):
            eval_dir_name = dir_name[2:]

        # We know we are in a directory
        is_directory = True

        ignore = False

        for ignore_re in path_ignore_pieces:
            # Ignore this directory?
            if ignore_re.search(eval_dir_name):
                ignore = True
                break
            # Remove any subdirectories matching the ignore list
            for subdir in sub_dir_list:
                if ignore_re.search(subdir):
                    sub_dir_list[:] = [d for d in sub_dir_list if not d == subdir]

        if not ignore:
            to_submit = add_to_push_list(
                file_list,
                base_path_index,
                dir_name,
                extensions,
                to_submit
            )
        else:
            # Ignore this directory and prevent its subdirectories from being walked further
            sub_dir_list[:] = []

    if not is_directory:
        to_submit = add_to_push_list(
            [fn],
            base_path_index,
            '.',
            extensions,
            to_submit
        )

    return to_submit


def rest_call(args, method, resource, data=None):
    err = None
    errstr = None
    res = None
    dict_res = None  # Calls *should* return JSON that we return as a dict

    uri = "%s/%s" % (args.endpoint, resource)

    headers = {'Content-Type': 'application/json',
               'STL-SID': args.sid}

    requests_args = {'headers': headers,
                     'timeout': 600}

    if data:
        requests_args['json'] = data

    if method == 'GET':
        res = requests.get(uri, **requests_args)
    elif method == 'POST':
        res = requests.post(uri, **requests_args)
    elif method == 'PUT':
        res = requests.put(uri, **requests_args)
    elif method == 'DELETE':
        res = requests.delete(uri, **requests_args)
    else:
        # XXX Something dire should happen here
        pass

    if res:
        if res.status_code == 200:
            try:
                dict_res = res.json()
            except json.decoder.JSONDecodeError as err:
                dict_res = None

            if not dict_res:
                err = 'no_json_returned_on_rest_call'
                errstr = "On call to endpoint %s we received a 200 OK status code but no JSON returned" % uri
        else:
            err = 'rest_call_err'
            errstr = "%s returned %i : %s" % (uri, res.status_code, res.reason)
    else:
        err = 'rest_call_no_response'
        errstr = "%s returned no response" % uri

    return res, dict_res, err, errstr


def destination_from_project_and_file(project_name, remote_fn):
    return ("project/%s/%s" % (project_name, remote_fn))


def send_file(args, local_fn, remote_fn, is_new):
    project_name = args.project
    buf = None

    with open(local_fn, "rb") as inf:
        buf = inf.read()

    data = {'code': "data:application/octet-stream;base64," + base64.b64encode(buf).decode(),
            'name': remote_fn}

    call_type = None

    if is_new:
        call_type = 'POST'
    else:
        call_type = 'PUT'

    destination = destination_from_project_and_file(project_name, remote_fn)

    return rest_call(args, call_type, destination, data)


def cmd_status(args):
    if not args.items:
        # They want status on the overall project.
        res, data, err, errstr = rest_call(args, 'GET', "/project/%s" % args.project)

        if res.status_code != 200 and \
                res.status_code != 404:
            abort(err, errstr)

        if res.status_code == 200:
            # We found it, should be a list of files now and their hashes
            if 'response' not in data:
                abort(rest_call_err, "Unexpect response from GET to /project/%s" % args.project)

                project = data['response']

                for item in project['code']:
                    print(project['code'])
        else:
            # A 404
            print("Project %s not yet created. Use the 'push' command to upload it." % args.project)


def find_common_base_dir(items):
    if not items.keys():
        return

    # Look for a common base directory
    dir_name = list(items.keys())[0].split('/')[0]
    if len(list(filter(lambda x: x.split('/')[0] == dir_name, items))) == len(items):
        # All the files are prefixed with the same directory name, so we can remove it
        return dir_name
    else:
        return


def cmd_push(args):
    if not args.items:
        abort('required_arg_not_found', 'Items argument is required for PUSH command.')

    to_submit = None
    local_items = {}

    base_path_index = None

    for fn in args.items:
        local_items = process_dir(local_items, fn, [x.lower() for x in args.extensions])

    common_base_directory = find_common_base_dir(local_items)

    # Look for `.gitignore` files
    gitignore = None
    for item in local_items:
        filename = local_items[item]['fn']
        if filename == '.gitignore':
            gitignore = True
    if gitignore:
        local_items = scrub_ignored_files(local_items)

    if len(local_items) == 0:
        # Probably print a message here once we get verbose output
        exit(0)

    new_local_items = dict()
    if common_base_directory:
        for filename, file_data in local_items.items():
            # Remove the `dir_name` from the filename in the file_data
            filename = file_data["fn"] = file_data["raw_fn"].replace(common_base_directory + '/', '')
            # Add the cleaned file data to our new dict with a cleaned filename as the key
            new_local_items[filename] = file_data
        local_items = new_local_items
    else:
        for file_data in local_items.values():
            file_data["fn"] = file_data["raw_fn"]

    print("Synchronizing files for project: %s" % args.project)
    
    # Is this a new project?
    project = None
    remote_items = {}

    res, data, err, errstr = rest_call(args, 'GET', "/project/%s" % args.project)

    if res.status_code != 200 and \
            res.status_code != 404:
        abort(err, errstr)

    if res.status_code == 200:
        # We found it, should be a list of files now and their hashes
        if 'response' not in data:
            abort(rest_call_err, "Unexpect response from GET to /project/%s" % args.project)

        project = data['response']

        for item in project['code']:
            remote_items[item['name']] = item
    else:
        # We got a 404, so it's a new project we'll implicitly create.
        # Noting to do right here though
        pass

    files_to_delete = []
    files_to_refresh = []
    files_to_send_new = []

    for remote_item_name in remote_items:
        print(str("Remote item %s" % remote_item_name))
        if remote_item_name in local_items:
            # Ok, it's in the uploaded project and our local project. Has it changed?
            if remote_items[remote_item_name]['sha256'] != local_items[remote_item_name]['sha256']:
                # It's changed, so let's submit it
                files_to_refresh.append(remote_item_name)
        else:
            # It's remote but not local, so we want to delete it
            files_to_delete.append(remote_item_name)

    for local_item_name in local_items:
        print(str("Local item %s" % local_item_name))
        if local_item_name not in remote_items:
            # It's new, we need to submit it
            files_to_send_new.append(local_item_name)

    changes = 0

    if files_to_send_new:
        print("Sending new files:")
        files_to_send_new = sorted(files_to_send_new)

        # Prioritize build files
        prioritized_files = ['package.json', 'requirements.txt']  # Move to constants section at top of file
        priority_files = list()
        for item in files_to_send_new:
            if any(file in item for file in prioritized_files):
                priority_files.append(item)
        if priority_files:
            non_priority_files = list(filter(lambda x: x not in priority_files, files_to_send_new))
            files_to_send_new = priority_files + non_priority_files
        for item in files_to_send_new:
            changes += 1
            print("\t" + local_items[item]['fn'])
            send_file(args, local_items[item]['raw_fn'], local_items[item]['fn'], True)

    if files_to_refresh:
        print("Refreshing changed files:")
        for item in sorted(files_to_refresh):
            changes += 1
            print("\t" + local_items[item]['fn'])
            send_file(args, local_items[item]['raw_fn'], local_items[item]['fn'], False)

    if files_to_delete:
        print("Deleting removed files:")
        for item in sorted(files_to_delete):
            changes += 1
            print("\t" + remote_items[item]['name'])
            rest_call(args, 'DELETE', destination_from_project_and_file(args.project, remote_items[item]['name']))

    if changes:
        print()
        print("%i items total changed" % changes)
    else:
        print("Nothing to do; all up to date!")


def cmd_test(args):
    if not args.json:
        print("Beginning test of project %s" % args.project)

    res, data, err, errstr = rest_call(args, 'POST', "test_project/%s" % args.project)

    if res.status_code != 200:
        abort(err, errstr)

    args.stlid = data['stlid']

    if not args.json:
        print("Test %s started, waiting for result." % args.stlid)

    done = False

    while not done:
        res, data, err, errstr = rest_call(args, 'GET', "/run_tests/%s" % args.stlid)

        if err:
            abort(err, errstr)

        if 'response' in data:
            if 'status_msg' in data['response']:
                if data['response']['status_msg'] == 'COMPLETE':
                    done = True
                    if not args.json:
                        print("\tSTATUS: Complete; getting results...")
                        print()

        if not done:
            if data['response']['status_msg'] == 'SETUP':
                if not args.json:
                    print("\tSTATUS: Setting up")
            else:
                if not args.json:
                    print("\tSTATUS: Running %s%% Complete" % data['response']['percent_complete'])

            sleep(5)

    show_test_results(args)


def fetch_test_results(args):
    try:
        return rest_call(args, 'GET', "/test_result/%s" % args.stlid)
    except:
        res = requests.models.Response()
        res.status_code = 598
        return [
            res,
            None,
            "rest_call_err",
            "There has been a network error with GET /test_result"
        ]


def show_test_results(args):
    res, data, err, errstr = fetch_test_results(args)

    try_count = 1
    while res.status_code != 200 and try_count <= max_retries_get_test_result:
        if not args.json:
            print("\tRetrying \"GET /test_result\"... (%s retry attempts)" % try_count)
        res, data, err, errstr = fetch_test_results(args)
        try_count = try_count + 1
        sleep(1)

    if res.status_code != 200:
        abort(err, errstr)

    if not args.json:
        print("%-30s %-12s %-6s %-10s %s" % ('FILENAME', 'TEST ID', 'SEV', 'LINES', 'TEST'))

    #    data['result'].sort(key = lambda x: (data['result'][x]['test_suite_test']['ftl_severity_ordinal'], data['result'][x]['code']['name'], data['result'][x]['test_suite_test']['ftl_test_id'], data['result'][x]['start_line']),
    #                        reverse = False)

    data['test_run_result'].sort(key=lambda x: (x['test_suite_test']['ftl_severity_ordinal'],
                                                x['code']['name'],
                                                x['test_suite_test']['ftl_test_id'],
                                                x['start_line']),
                                 reverse=False)

    #    data['result'].sort(key = lambda x: (x['test_suite_test']['ftl_severity_ordinal']),
    #                        reverse = False)

    if not args.json:
        for result in data['test_run_result']:
            print("%-30s %-12s %-6s %4i - %4i %s" %
                (result['code']['name'],
                result['test_suite_test']['ftl_test_id'],
                result['test_suite_test']['ftl_severity'],
                result['start_line'],
                result['end_line'],
                result['test_suite_test']['ftl_short_description']))
    else:
        print(json.dumps(data['test_run_result']))


def cmd_del(args):
    res, data, err, errstr = rest_call(args, 'DELETE', "/project/%s" % args.project)

    if err:
        abort(err, errstr)

    if 'response' in data:
        if data['response'] == 'OK':
            print("\"%s\" has been deleted." % args.project)


def cmd_view(args):
    for stlid in args.items:
        args.stlid = stlid
        show_test_results(args)


def determine_project(args):
    err = None
    errstr = None
    project = None

    # Easiest: Did they explicitly specify it on the command-line?
    if args.project:
        # Yes, they did!
        project = args.project
    elif 'FTL_PROJECT' in os.environ:
        # Ok, they specified it in the environment
        project = os.environ['FTL_PROJECT']
    else:
        # In the future we might like to try to guess from the
        # directory you're submitting (if you submit only one).
        # But, for now, we just throw an error:
        err = 'unable_to_determine_project'
        errstr = textwrap.fill(
            "Unable to determine project. Please either specify explicitly using the --project flag, or in the environment with the variable FTL_PROJECT. Note this string is an arbitrary one that you choose to allow yourself to have more than one project you're working on at any given time.")

    return project, err, errstr


def determine_sid(args):
    err = None
    errstr = None
    sid = None

    if args.sid:
        # They explicitly specified
        sid = args.sid
    elif 'FTL_SID' in os.environ:
        # In the environment
        sid = os.environ['FTL_SID']
    elif 'STL_INTERNAL_SID' in os.environ:
        # Old internal SID name, will delete when we migrate internal names
        sid = os.environ['STL_INTERNAL_SID']
    else:
        err = 'unable_to_determine_sid'
        errstr = textwrap.fill(
            "Unable to determine SID. Please either specify explicitly using the --sid flage, or in the environment with the varliable FTL_SID")

    if sid is not None:
        if not re.match('^[A-z0-9]{40}$', sid):
            err = 'textually_invalid_sid'
            errstr = textwrap.fill(
                'SID "%s" does not appear to be valid; a valid SID is 40 characters long, comprised of the characters A-z and 0-9.' % sid)

    return sid, err, errstr


def scrub_ignored_files(local_files):
    if not local_files:
        return
    
    repo_path = os.getcwd()
    repo = None
    temp_repo = None # If `.git` is not found we init and then destroy a repo
    
    # Repo object used to programmatically interact with Git repositories
    try:
        repo = Repo(repo_path)
    except:
        # No GIT repository was found
        repo = Repo.init(repo_path)
        temp_repo = True

    # check that the repository loaded correctly
    if repo and not repo.bare:
        git = repo.git
        clean = git.clean(n=True, d=True, X=True)

        # Iterate through local_files and remove any to be ignored
        clean_files = dict()
        for item in local_files:
            filepath = local_files[item]['raw_fn']
            ignore = None
            for line in clean.splitlines():
                line = line.replace('Would remove ', '')
                if filepath.startswith(line):
                    ignore = True
            if not ignore:
                clean_files[item] = local_files[item]

        print("Found a `.gitignore` file. Evaluating files...")
        print("%d of %d local files match .gitignore patterns." % (
            len(local_files) - len(clean_files),
            len(local_files)
        ))
        print("%d files ready to upload..." % len(clean_files))
        local_files = clean_files

        if temp_repo:
            try:
                shutil.rmtree(repo_path + os.path.sep + '.git')
            except:
                print('Failed to remove temporary GIT initialization!')
        
    return local_files


def main():
    commands = {'push': cmd_push,
                'status': cmd_status,
                'del': cmd_del,
                'test': cmd_test,
                'view': cmd_view}

    ftl_project_string = 'UNSET'

    if 'FTL_PROJECT' in os.environ:
        ftl_project_string = '"' + os.environ['FTL_PROJECT'] + '"'

    default_endpoint = None

    if 'FTL_ENDPOINT' in os.environ:
        default_endpoint = os.environ['FTL_ENDPOINT']
    elif 'STL_ENDPOINT' in os.environ:
        # Temporarily allow the old variable name until we get rid of it
        default_endpoint = os.environ['STL_ENDPOINT']
    else:
        default_endpoint = 'https://api.bugcatcher.fasterthanlight.dev'

    parser = argparse.ArgumentParser(description='FTL Client for running tests')

    parser.add_argument('command', type=str, help="Command. One of: " + ' '.join(sorted(commands.keys())))

    parser.add_argument('items', type=str, nargs='*',
                        help='Files and directories to process, or test IDs to work on')

    parser.add_argument('--project', '-p', type=str,
                        help="Project name to operate on. If unspecified, will use the value of the environment variable FTL_PROJECT (currently %s)" % ftl_project_string)

    parser.add_argument('--endpoint', '-e', default=default_endpoint,
                        help="Endpoint to connect to. If unspecified, will use program default, or the environment variable FTL_ENDPOINT. Currently set to %s" % default_endpoint)

    parser.add_argument('--async', '-a', action='store_true',
                        help='Test in asynchronous mode; return immediately with a test ID')

    parser.add_argument('--sid', '-s',
                        help="SID to use for authentication. If not specified, will use environment variable FTL_SID")

    parser.add_argument('--json', '-j', action='store_true',
                        help="Results of \"test\" and \"view\" commands will be returned as a JSON byte array.")

    parser.add_argument('--extension', dest='extensions', action="append",
                        help="Extensions to submit. If unspecified, defaults to %s. Adding extensions adds to this list, rather than replacing it" % default_extensions,
                        default=default_extensions)

    args = parser.parse_args()

    if args.command is None:
        print("Must specify commmand. One of: " + ' '.join(sorted(commands.keys())), file=sys.stderr)
        exit(exit_error['command_unspecified'])

    if args.command not in commands:
        print('Command "%s" not recognized. Must be one of: ' % args.command + ' '.join(sorted(commands.keys())),
              file=sys.stderr)
        exit(exit_error['unknown_command'])

    project, err, errstr = determine_project(args)

    if err:
        print(errstr, file=sys.stderr)
        exit(exit_error[err])

    args.project = project

    sid, err, errstr = determine_sid(args)

    if err:
        print(errstr, file=sys.stderr)
        exit(exit_error[err])

    args.sid = sid

    commands[args.command](args)
