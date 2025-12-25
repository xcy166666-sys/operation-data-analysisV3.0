import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.bailian_service import BailianService

async def test_api_connection():
    print('Testing Alibaba API connection...')
    
    service = BailianService()
    
    if not service.api_key:
        print('ERROR: DASHSCOPE_API_KEY not configured')
        return False
    
    try:
        # Simple test call
        response = await service._call_dashscope_api(
            prompt='Hello, please respond with "API test successful"',
            file_base64='',
            file_name='test.txt'
        )
        
        print('SUCCESS: API call successful!')
        print(f'Response keys: {list(response.keys())}')
        
        # Extract content
        if service.use_openai_format:
            if 'choices' in response and response['choices']:
                content = response['choices'][0].get('message', {}).get('content', '')
                print(f'Content: {content[:100]}...')
        else:
            output = response.get('output', {})
            choices = output.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                content = message.get('content', '') or message.get('text', '')
                print(f'Content: {content[:100]}...')
        
        return True
        
    except Exception as e:
        print(f'ERROR: API call failed - {str(e)}')
        return False

if __name__ == '__main__':
    result = asyncio.run(test_api_connection())
    sys.exit(0 if result else 1)
