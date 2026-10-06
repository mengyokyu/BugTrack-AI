def register(client, email):
    return client.post('/api/auth/register', json={'name': email.split('@')[0], 'email': email, 'password': 'password123'})


def test_health_live_and_ready(client):
    assert client.get('/health/live').json['status'] == 'ok'
    assert client.get('/health/ready').status_code == 200


def test_cross_user_bug_isolation(client):
    register(client, 'one@example.com')
    created = client.post('/api/bugs', json={'title': 'Private', 'description': 'secret'}).json
    client.post('/api/auth/logout')
    register(client, 'two@example.com')
    assert client.get(f"/api/bugs/{created['id']}").status_code == 403
    assert client.put(f"/api/bugs/{created['id']}", json={'status': 'RESOLVED'}).status_code == 403


def test_validation_and_csrf(client):
    assert register(client, 'bad@example.com').status_code == 201
    assert client.post('/api/bugs', json={'title': '', 'description': ''}).status_code == 400
    client.application.config['TESTING'] = False
    csrf = client.get('/api/auth/csrf').json['csrf_token']
    assert client.post('/api/bugs', json={'title': 'No token', 'description': 'blocked'}).status_code == 400
    assert client.post('/api/bugs', json={'title': 'With token', 'description': 'accepted'}, headers={'X-CSRFToken': csrf}).status_code == 201


def test_project_membership_isolation(client):
    register(client, 'owner@example.com')
    project = client.post('/api/projects', json={'name': 'Core', 'key': 'CORE'}).json
    client.post('/api/auth/logout')
    register(client, 'member@example.com')
    member = client.get('/api/auth/me').json
    client.post('/api/auth/logout')
    assert client.post('/api/auth/login', json={'email': 'owner@example.com', 'password': 'password123'}).status_code == 200
    assert client.post(f"/api/projects/{project['id']}/members", json={'user_id': member['id'], 'role': 'member'}).status_code == 201
    client.post('/api/auth/logout')
    client.post('/api/auth/login', json={'email': 'member@example.com', 'password': 'password123'})
    created = client.post('/api/bugs', json={'project_id': project['id'], 'title': 'Member bug', 'description': 'visible'})
    assert created.status_code == 201
    assert client.get('/api/bugs').json['total'] == 1
