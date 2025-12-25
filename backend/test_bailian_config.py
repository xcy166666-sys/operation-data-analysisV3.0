from app.services.bailian_service import BailianService
service = BailianService()
print('闃块噷API閰嶇疆鐘舵€?')
api_status = 'configured' if service.api_key else 'not configured'
print(f'API Key: {api_status}')
print(f'Model: {service.model}')
print(f'API URL: {service.api_url}')
print(f'Use OpenAI format: {service.use_openai_format}')
