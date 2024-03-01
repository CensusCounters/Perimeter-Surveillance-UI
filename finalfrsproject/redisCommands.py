import redis
# Connect to Redis
#redis_conn = redis.from_url('redis://census_counters-redis:6379')
redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)

