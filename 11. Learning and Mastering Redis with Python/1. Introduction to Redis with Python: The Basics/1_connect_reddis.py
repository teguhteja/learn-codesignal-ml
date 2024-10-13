import redis

# Connect to the Redis server
client = redis.Redis(host='localhost', port=6379, db=0)

# Verify the connection by setting and getting a value
client.set('name', 'Redis Learner')
print(f"Stored string in Redis: {client.get('name').decode('utf-8')}")