import requests
import json
import sseclient

class NovelCrawlerTester:
    def __init__(self, base_url):
        self.base_url = base_url

    def test_start_crawl(self, novel_name):
        print(f"Testing start_crawl with novel name: {novel_name}")
        try:
            response = requests.post(f'{self.base_url}/start', 
                                     json={'novel_name': novel_name}, 
                                     stream=True)
            
            client = sseclient.SSEClient(response)
            for event in client.events():
                if event.data == 'SEARCH_COMPLETED':
                    print("Search completed successfully.")
                    break
                elif event.data == 'SEARCH_FAILED':
                    print("Search failed.")
                    break
                elif event.data.startswith('ERROR:'):
                    print(f"An error occurred: {event.data}")
                    break
                else:
                    print(event.data.strip())
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

def main():
    base_url = 'http://192.168.1.206:5000'  # Replace with your server's IP address
    tester = NovelCrawlerTester(base_url)
    
    print("Testing connection to server...")
    tester.test_start_crawl('Release That Witch')

if __name__ == '__main__':
    main()