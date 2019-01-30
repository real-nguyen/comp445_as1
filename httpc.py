import requests
import json

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
    if headers:
        # Parse headers
        headers = json.loads(headers)
        response = requests.get(URL, headers=headers)
    else:
        response = requests.get(URL)
    response_str = ''
    if verbose:
        response_str += 'Status: {0}\n'.format(response.status_code)
        for key, value in response.headers.items():
            response_str += '{0}: {1}\n'.format(key, value)
    response_str += response.text
    print(response_str)

get('http://httpbin.org/get?course=networking&assignment=1')
get('http://httpbin.org/get?course=networking&assignment=1', headers='{"User-Agent":"Concordia-HTTP/1.0"}')
