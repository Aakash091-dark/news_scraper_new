import requests
from bs4 import BeautifulSoup

def extract_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error if the request failed

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        # Extract and clean up the visible text
        text = soup.get_text(separator=' ', strip=True)

        return text

    except requests.exceptions.RequestException as e:
        return f"Error fetching the URL: {e}"

# Example usage
if __name__ == "__main__":
    url = input("Enter a URL to extract text from: ")
    extracted_text = extract_text_from_url(url)
    print("\n--- Extracted Text ---\n")
    print(extracted_text)
