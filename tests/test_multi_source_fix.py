import requests
import os

# Test the multi-source extraction endpoint with a buyer profile file
def test_multi_source_extraction():
    url = 'http://localhost:8000/api/multi-source-extraction/'
    
    # Use the same file that caused the error
    file_path = '/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend/Rob Brubaker and Sheridan Richey PAIR - FINAL Buyer Profile - Cohort 53.docx'
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        with open(file_path, 'rb') as file:
            files = {'buyer_profile': file}
            
            print("🚀 Testing multi-source extraction with buyer profile...")
            response = requests.post(url, files=files)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_multi_source_extraction()