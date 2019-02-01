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
# Will find command line flags and their parameters
FLAGS_REGEX = r"(?P<flag>-{1,2}\S*)(?:[=:]?|\s+)(?P<params>[^-\s].*?)?(?=\s+[-\/]|$)"
# Taken from https://stackoverflow.com/questions/6038061/regular-expression-to-find-urls-within-a-string
URL_REGEX = r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
FLAG_VERBOSE = '-v'
FLAG_HEADERS = '-h'
FLAG_INLINE_DATA = '-d'
FLAG_FILE = '-f'

def help():
    description = 'httpc is a curl-like application but supports HTTP protocol only.'
    usage = 'Usage:\n\thttpc command [arguments]'
    commands = """The commands are:\n\tget\texecutes a HTTP GET REQUEST and prints the response.
        post\texecutes a HTTP POST request and prints the response.
        help\tprints this screen."""
    use = 'Use "httpc help [command]" for more information about a command.'
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
    request_str = f'GET {path}?{query} HTTP/1.0\r\nHost: {host}\r\n'
    
    for key, value in get_headers(flags):
        request_str += f'{key}: {value}\r\n'

    request_str += '\r\n'
    send_request(host, request_str)

def post(URL, flags):
    if not are_flags_valid(flags):
        print('Invalid query. You cannot have both -f and -d flags set simultaneously.')
        return

    # Scheme is HTTP by default, and the only one we need for this assignment
    # In POST, the data to send to the host is NOT in the URL
    parsed_url = urllib.parse.urlparse(URL)
    host = parsed_url[1]
    path = parsed_url[2]

    if FLAG_FILE in flags:
        data = get_data(flags)
        filename = data[1].strip('\'')
        request_str = get_file_contents(filename)
        send_request(host, request_str.replace('\n', '\r\n'))
        return

    request_str = f'POST {path} HTTP/1.0\r\nHost: {host}\r\n'
        
    for key, value in get_headers(flags):
        request_str += f'{key}: {value}\r\n'
    
    data = get_data(flags)
    flag = data[0]
    value = data[1].strip('\'')
    content_len = len(value)
    # Content-Type and Content-Length are mandatory headers, write them here as part of the request
    # If already passed as parameters to -h, the headers here will overwrite them
    request_str += f'Content-Length: {content_len}\r\n'

    if flag == FLAG_INLINE_DATA:
        if is_json(value):
            request_str += 'Content-Type: application/json\r\n'
        else:
            request_str += 'Content-Type: application/x-www-form-urlencoded\r\n'
     
    # For -f: multipart/form-data

    request_str += '\r\n'
    # Data to send is stored in request header
    request_str += value
    send_request(host, request_str)
    
def send_request(host, request_str):
    # Send request and print response
    request_bytes = bytes(request_str, encoding='ASCII')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, TCP_PORT))
    s.send(request_bytes)
    result = s.recv(BUFFER_SIZE)

    # Get result from byte stream, divide result into 10 kB chunks
    buffer_str = ''
    while (len(result) > 0):
        # Decode bytes from result into string from ASCII mapping
        buffer_str += result.decode('ASCII')
        result = s.recv(BUFFER_SIZE)
    s.close()

    if is_verbose(flags):
        # Prints both response header and JSON response
        print(buffer_str)
    else:
        split = buffer_str.split('\r\n\r\n')
        # Only print JSON response
        print(split[1])

def get_url(query):
    url = re.search(URL_REGEX, query)
    return url.group(0)

def get_flags(query):
    flags = re.findall(FLAGS_REGEX, query)
    return dict(flags)

def get_headers(flags):
    # Response header
    headers = []
    for flag, value in flags.items():
        if flag != FLAG_HEADERS:
            continue
        split = value.split(':')
        headers.append((split[0], split[1]))
    return headers

def get_data(flags):
    # Post data
    # Cannot have both -f and -d at the same time
    for flag, value in flags.items():
        if flag != FLAG_INLINE_DATA and flag != FLAG_FILE:
            continue
        return (flag, value)
    return None

def get_file_contents(path):
    f = open(path, "r")
    return f.read()

# Taken from https://stackoverflow.com/questions/11294535/verify-if-a-string-is-json-in-python
def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def is_verbose(flags):
    return FLAG_VERBOSE in flags

def are_flags_valid(flags):
    return not (FLAG_INLINE_DATA in flags and FLAG_FILE in flags)


test_get = "httpc get 'http://httpbin.org/get?course=networking&assignment=1' -h Content-Type:application/json -v -h User-Agent:httpc"
form_data = "comments=abcde&custemail=abc%40def.com&custtel=1234567890&delivery=21%3A00&size=small&topping=cheese&topping=onion"
json_data = '{"Assignment": 1}'
test_post_d = f"httpc post 'http://httpbin.org/post' -d '{form_data}' -v"
test_post_f = f"httpc post 'http://httpbin.org/post' -f '{os.path.join(POST_FILES, 'request.txt')}' -v"
# Takes relative path of file as input

# url = get_url(test_get)
# flags = get_flags(test_get)
# get(url, flags)
url = get_url(test_post_f)
flags = get_flags(test_post_f)
post(url, flags)
