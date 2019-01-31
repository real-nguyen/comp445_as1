import socket
import json
import urllib.parse
import re

TCP_PORT = 80
BUFFER_SIZE = 4096 # in bytes
# Taken from http://amdonnelly.blogspot.com/2014/05/regular-expression-command-line.html
# Will find command line flags and their parameters
FLAGS_REGEX = r"(?P<flag>-{1,2}\S*)(?:[=:]?|\s+)(?P<params> [^-\s].*?)?(?=\s+[-\/]|$)"
# Taken from https://stackoverflow.com/questions/6038061/regular-expression-to-find-urls-within-a-string
URL_REGEX = r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
FLAG_VERBOSE = '-v'
FLAG_HEADERS = '-h'
FLAG_DATA = '-d'
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
    parsed_url = urllib.parse.urlparse(URL)
    host = parsed_url[1]
    path = parsed_url[2]
    query = parsed_url[4]    
    request_str = f'GET {path}?{query} HTTP/1.0\r\nHost: {host}\r\n\r\n'
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
    return flags

def get_headers(header_str):
    headers = []
    split = header_str.split(':')
    key, value = split[0], split[1]
    # Returns JSON object
    return json.loads('{{"{0}":"{1}"}}'.format(key, value))

def is_verbose(flags):
    for flag, params in flags:
        if flag == FLAG_VERBOSE:
            return True
    return False

test_get = "httpc get 'http://httpbin.org/get?course=networking&assignment=1' -v -h Content-Type:application/json -h User-Agent:httpc"
url = get_url(test_get)
flags = get_flags(test_get)
get(url, flags)
#get('http://httpbin.org/get?course=networking&assignment=1', headers='User-Agent:Concordia-HTTP/1.0')
