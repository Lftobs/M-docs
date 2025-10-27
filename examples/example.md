# Authentication

## Login
**Description:** Get token for auth  
**Save Response Variable:** auth_token

```curl
curl -X POST https://api.example.com/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "1234"}'
```

# User Operations

## Get User Profile
**Description:** Fetch user profile  
**Requires:** auth_token

```curl
curl -X GET https://api.example.com/user/profile \
  -H "Authorization: Bearer {{auth_token}}"
```

## Update User Profile
**Description:** Update user profile information
**Requires:** auth_token

```curl
curl -X PUT https://api.example.com/user/profile \
  -H "Authorization: Bearer {{auth_token}}" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```