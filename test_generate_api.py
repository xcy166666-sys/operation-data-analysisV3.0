"""
测试生成报告API
"""
import requests
import json

# 登录获取token
login_url = "http://localhost:8000/api/v1/auth/login"
login_data = {
    "username": "admin",
    "password": "admin123!"
}

print("1. 登录...")
response = requests.post(login_url, json=login_data)
print(f"登录响应: {response.status_code}")
if response.status_code == 200:
    token = response.json()["data"]["access_token"]
    print(f"Token: {token[:50]}...")
else:
    print(f"登录失败: {response.text}")
    exit(1)

# 设置headers
headers = {
    "Authorization": f"Bearer {token}"
}

# 创建会话
print("\n2. 创建会话...")
create_session_url = "http://localhost:8000/api/v1/operation/sessions"
response = requests.post(create_session_url, json={}, headers=headers)
print(f"创建会话响应: {response.status_code}")
if response.status_code == 200:
    session_id = response.json()["data"]["id"]
    print(f"Session ID: {session_id}")
else:
    print(f"创建会话失败: {response.text}")
    exit(1)

# 上传文件
print("\n3. 上传文件...")
upload_url = "http://localhost:8000/api/v1/operation/upload"
files = {
    'file': ('test.xlsx', open('backend/test_data.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
}
data = {
    'session_id': session_id
}
response = requests.post(upload_url, files=files, data=data, headers=headers)
print(f"上传文件响应: {response.status_code}")
if response.status_code == 200:
    file_id = response.json()["data"]["file_id"]
    print(f"File ID: {file_id}")
else:
    print(f"上传文件失败: {response.text}")
    exit(1)

# 生成报告
print("\n4. 生成报告...")
generate_url = "http://localhost:8000/api/v1/operation/generate"
data = {
    'session_id': session_id,
    'file_id': file_id,
    'analysis_request': '生成一份关注新手留存的周度报告',
    'chart_generation_mode': 'html'
}
response = requests.post(generate_url, data=data, headers=headers)
print(f"生成报告响应: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"报告生成成功!")
    print(f"Report ID: {result['data']['report_id']}")
    print(f"文本长度: {len(result['data']['content']['text'])}")
    print(f"图表数量: {len(result['data']['content'].get('charts', []))}")
    print(f"HTML图表长度: {len(result['data']['content'].get('html_charts', ''))}")
else:
    print(f"生成报告失败: {response.status_code}")
    print(f"错误详情: {response.text}")
