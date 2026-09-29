def test_register_login_and_protection(client):
    assert client.get('/api/bugs').status_code==401
    r=client.post('/api/auth/register',json={'name':'Ada','email':'ada@example.com','password':'password123'}); assert r.status_code==201
    assert client.get('/api/auth/me').json['email']=='ada@example.com'
    client.post('/api/auth/logout'); assert client.post('/api/auth/login',json={'email':'ada@example.com','password':'password123'}).status_code==200
