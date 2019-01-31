import socket
import json
import urllib.parse

TCP_PORT = 80
BUFFER_SIZE = 4096 # in bytes

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

def get(URL, verbose=False, headers=''):
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
    
    if verbose:
        # Prints both response header and JSON response
        print(buffer_str)
    else:
        split = buffer_str.split('\r\n\r\n')
        # Only print JSON response
        print(split[1])

def form_header(header_str):
    split = header_str.split(':')
    key, value = split[0], split[1]
    # Returns JSON object
    return json.loads('{{"{0}":"{1}"}}'.format(key, value))

get('http://httpbin.org/get?course=networking&assignment=1', verbose=True)
#get('http://httpbin.org/get?course=networking&assignment=1', headers='User-Agent:Concordia-HTTP/1.0')
