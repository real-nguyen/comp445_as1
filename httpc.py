import socket
import urllib.parse
import re
import json
import os

# Get relative path
DIRNAME = os.path.dirname(__file__)
POST_FILES = os.path.join(DIRNAME, 'post_files')
TCP_PORT = 80
BUFFER_SIZE = 4096 # in bytes
# Taken from http://amdonnelly.blogspot.com/2014/05/regular-expression-command-line.html
APP_NAME = 'httpc'
COMMAND_HELP = 'help'
COMMAND_GET = 'get'
COMMAND_POST = 'post'
COMMAND_QUIT = 'quit'
FLAG_VERBOSE = '-v'
FLAG_HEADERS = '-h'
FLAG_INLINE_DATA = '-d'
FLAG_FILE = '-f'
HEADER_FORMAT = 'key:value'
LOCALHOST = 'localhost'
LOCALHOST_IP = '127\.0\.0\.1'
# Will find command line flags and their parameters
REGEX_FLAGS = r"(?P<flag>-{1,2}\S*)(?:[=:]?|\s+)(?P<params>[^-\s].*?)?(?=\s+[-\/]|$)"
# Taken from https://stackoverflow.com/questions/6038061/regular-expression-to-find-urls-within-a-string
REGEX_URL = r"(http://)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
# Taken from https://stackoverflow.com/questions/18696796/regexp-javascript-url-match-with-localhost
REGEX_LOCALHOST = rf"({LOCALHOST}|{LOCALHOST_IP})(:[0-9]+)?([/\.\w]+)*"
# Command regexes
REGEX_STARTS_WITH_APP_NAME = rf"^{APP_NAME}"
REGEX_NO_COMMAND = rf"^{APP_NAME}$"
REGEX_HELP = rf"^{APP_NAME} {COMMAND_HELP}\s?({COMMAND_GET}|{COMMAND_POST})?$"
REGEX_GET = rf"^({APP_NAME} {COMMAND_GET})"
REGEX_POST = rf"^({APP_NAME} {COMMAND_POST})"
REGEX_HEADER = r"(\s+:\s+)"

def help(command=''):
    desc_verbose = f'{FLAG_VERBOSE}\t\tPrints the detail of a response such as protocol, status, and headers.'
    desc_headers = f"{FLAG_HEADERS} {HEADER_FORMAT}\tAssociates headers to HTTP request with the format '{HEADER_FORMAT}'."
    if command == COMMAND_GET:
        usage = f'Usage: {APP_NAME} {COMMAND_GET} [{FLAG_VERBOSE}] [{FLAG_HEADERS} {HEADER_FORMAT}] URL'
        description = f'{COMMAND_GET} executes a HTTP GET request for a given URL.'
        flags = f"""
        {desc_verbose}
        {desc_headers}"""
        print('\n' + usage)
        print('\n' + description)
        print(flags + '\n')
    elif command == COMMAND_POST:
        usage = f'Usage: {APP_NAME} {COMMAND_POST} [{FLAG_VERBOSE}] [{FLAG_HEADERS} {HEADER_FORMAT}] [{FLAG_INLINE_DATA} inline-data] [{FLAG_FILE} file] URL'
        description = f'{COMMAND_POST} executes a HTTP POST request for a given URL with inline data or from a file.'
        flags = f"""
        {desc_verbose}
        {desc_headers}
        {FLAG_INLINE_DATA} string\tAssociates an inline data to the body of a HTTP POST request.
        {FLAG_FILE} file\t\tAssociates the content of a file to the body of a HTTP POST request."""
        flags_limit = f'Either [{FLAG_INLINE_DATA}] or [{FLAG_FILE}] can be used but not both.'
        print('\n' + usage)
        print('\n' + description)
        print(flags + '\n')
        print(flags_limit + '\n')
    else:
        description = f'{APP_NAME} is a curl-like application but supports HTTP protocol only.'
        usage = f'Usage: {APP_NAME} command [arguments]'
        commands = f"""The commands are:
        {COMMAND_GET}\texecutes a HTTP GET REQUEST and prints the response.
        {COMMAND_POST}\texecutes a HTTP POST request and prints the response.
        {COMMAND_HELP}\tprints this screen."""
        use = f'Use "{APP_NAME} {COMMAND_HELP} [command]" for more information about a command.'
        print('\n' + description)
        print(usage)
        print(commands + '\n')
        print(use)

def get(URL, flags):
    # Scheme is HTTP by default, and the only one we need for this assignment
    # In GET, the data to send is stored in the query, as part of the URL
    parsed_url = urllib.parse.urlparse(URL)
    host = parsed_url[1]
    path = parsed_url[2]
    query = parsed_url[4]
    if query != None and query != '':
        request_str = f'GET {path}?{query} HTTP/1.0\r\nHost: {host}\r\n'
    else:
        request_str = f'GET {path} HTTP/1.0\r\nHost: {host}\r\n'

    for key, value in get_headers(flags):
        request_str += f'{key}: {value}\r\n'

    request_str += '\r\n'
    print(request_str)    
    send_request(host, request_str, is_verbose(flags))

def post(URL, flags):
    # Scheme is HTTP by default, and the only one we need for this assignment
    # In POST, the data to send to the host is NOT in the URL
    parsed_url = urllib.parse.urlparse(URL)
    host = parsed_url[1]
    path = parsed_url[2]

    request_str = f'POST {path} HTTP/1.0\r\nHost: {host}\r\n'
        
    for key, value in get_headers(flags):
        request_str += f'{key}: {value}\r\n'
    
    data = get_data(flags)
    flag = data[0]
    
    if flag == FLAG_INLINE_DATA:
        value = data[1].strip('\'')
    elif flag == FLAG_FILE:
        # Input from console should be path relative to httpc.py
        # Will only work if input file is in app folder or subfolder, not from outside!
        filename = os.path.join(DIRNAME, data[1].strip('\''))
        value = get_file_contents(filename)

    content_len = len(value)
    # Content-Type and Content-Length are mandatory headers, write them here as part of the request
    # If already passed as parameters to -h, the headers here will overwrite them
    # For this assignment, requests will only have JSON and form data in their bodies
    request_str += f'Content-Length: {content_len}\r\n'
    
    if is_json(value):
        request_str += 'Content-Type: application/json\r\n'
    else:
        request_str += 'Content-Type: application/x-www-form-urlencoded\r\n'
    
    # For -f: multipart/form-data

    request_str += '\r\n'
    # Data to send is stored in request header
    request_str += value
    send_request(host, request_str, is_verbose(flags))
    
def send_request(host, request_str, verbose):
    # Send request and print response
    request_bytes = bytes(request_str, encoding='ASCII')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, TCP_PORT))
        s.send(request_bytes)
        result = s.recv(BUFFER_SIZE)

        # Get result from byte stream, divide result into 10 kB chunks
        buffer_str = ''
        while len(result) > 0:
            # Decode bytes from result into string from ASCII mapping
            buffer_str += result.decode('ASCII')
            result = s.recv(BUFFER_SIZE)
        s.close()
    except TimeoutError:
        print('Connection timed out.')
        s.close()
        return

    if verbose:
        # Prints both response header and JSON response
        print(buffer_str)
    else:
        split = buffer_str.split('\r\n\r\n')
        # Only print JSON response
        print(split[1])

def get_url(query):
    print(query)
    url = None
    url = re.search(REGEX_LOCALHOST, query)
    print(f'localhost url: {url}')
    if url != None:
        return url.group(0)
    url = re.search(REGEX_URL, query)
    print(f'regular url: {url}')
    if url != None:
        return url.group(0)
    return url

def get_flags(query):
    flags = re.findall(REGEX_FLAGS, query)
    return flags

def get_headers(flags):
    # Response header
    headers = []
    for flag, value in flags:
        if flag != FLAG_HEADERS:
            continue
        split = value.split(':')
        headers.append((split[0], split[1]))
    return headers

def get_data(flags):
    # Post data
    # Cannot have both -f and -d at the same time
    for flag, value in flags:
        if flag != FLAG_INLINE_DATA and flag != FLAG_FILE:
            continue
        return (flag, value)
    return None

def get_file_contents(path):
    # Get file contents to use as request body    
    f = open(path, "r")
    return f.read()

# Taken from https://stackoverflow.com/questions/11294535/verify-if-a-string-is-json-in-python
def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True

def is_verbose(flags):
    for flag, value in flags:
        if flag == FLAG_VERBOSE:
            return True
    return False

def are_flags_valid(flags):
    return not (FLAG_INLINE_DATA in flags and FLAG_FILE in flags)

def parse_query(query):
    match = re.search(REGEX_STARTS_WITH_APP_NAME, query)
    if match == None:
        # httpc is not the first word in the query
        print('Unknown command.')
        return
    match = re.search(REGEX_NO_COMMAND, query)
    if match != None:
        # User wrote 'httpc' and nothing else
        print(f"Type '{APP_NAME} {COMMAND_HELP}' for usage information .")
        return
    match = re.search(REGEX_HELP, query)
    if match != None:
        # User needs to see usage information
        split = query.split(' ')
        if len(split) == 3:
            # User needs usage information on specific command
            help(split[2])
        else:
            help()
        return
    match = re.search(REGEX_GET, query)
    if match != None:
        url = get_url(query)
        if url == None:
            print(f"A valid URL is needed for command '{APP_NAME} {COMMAND_GET}'.")
            return
        flags = get_flags(query)
        for flag, value in flags:
            if flag == FLAG_HEADERS and value == '':
                print(f"The flag {FLAG_HEADERS} needs a parameter with the format {HEADER_FORMAT}.")
                return
        get(url, flags)
        return
    match = re.search(REGEX_POST, query)
    if match != None:
        url = get_url(query)
        if url == None:
            print(f"A valid URL is needed for command '{APP_NAME} {COMMAND_GET}'.")
            return
        flags = get_flags(query)
        has_inline_data, has_file = False, False
        for flag, value in flags:
            if flag == FLAG_INLINE_DATA:
                has_inline_data = True
            if flag == FLAG_FILE:
                has_file = True
            if has_inline_data and has_file:
                print(f"You cannot have both the {FLAG_FILE} and {FLAG_INLINE_DATA} flags set simultaneously.")
                return
            if flag == FLAG_HEADERS and value == '':
                print(f"The flag {FLAG_HEADERS} needs a parameter with the format {HEADER_FORMAT}.")
                return
            if (flag == FLAG_INLINE_DATA or flag == FLAG_FILE) and value == '':
                print(f"The flag {flag} needs a parameter.")
                return
        post(url, flags)
        return
    print(f'Unknown or invalid command for {APP_NAME}. Please check that your commands and/or flags are well formatted.')

while True:
    print('> ', end='')
    query = input()
    if query == COMMAND_QUIT:
        break
    parse_query(query)