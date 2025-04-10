import os
import sys
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        return
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("Successfully created Anthropic client")
        
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": "Hello, Claude\!"}
            ]
        )
        
        print(f"Response: {response.content[0].text}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
