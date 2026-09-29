def auth(client): client.post('/api/auth/register',json={'name':'Ada','email':'ada@example.com','password':'password123'})
def test_bug_crud(client):
    auth(client); r=client.post('/api/bugs',json={'title':'Crash','description':'It crashes','severity':'HIGH'}); assert r.status_code==201; bid=r.json['id']
    assert client.get(f'/api/bugs/{bid}').status_code==200
    assert client.put(f'/api/bugs/{bid}',json={'status':'RESOLVED'}).json['status']=='RESOLVED'
    assert client.post(f'/api/bugs/{bid}/comments',json={'content':'Investigating'}).status_code==201
    assert client.delete(f'/api/bugs/{bid}').status_code==200
