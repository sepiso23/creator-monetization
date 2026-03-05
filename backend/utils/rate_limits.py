from django.core.cache import cache

def check_login_attemps(email):
    key = f"login_attemps_{email}"
    attempts = cache.get(key, 0)

    if attempts >= 5:
        return False, "Account locked. Try again in 30 minutes."

    return True, attempts


def increment_login_attemps(email):
    key = f"login_attemps_{email}"
    attempts = cache.get(key, 0)
    cache.set(key, attempts + 1, timeout=1800) # 30 minutes


def reset_login_attemps(email):
    key = f"login_attemps_{email}"
    cache.delete(key)


def check_rate_limit(key, limit, timeout):
    cache_key = f"rate_limit_{key}"
    count = cache.get(cache_key, 0)

    if count >= limit:
        return False, "Rate limit exceeded. Try again later."

    cache.set(cache_key, count + 1, timeout=timeout)
    return True, count + 1

def check_payment_rate_limit(wallet_id, limit=5, timeout=3600):
    key = f"payment_rate_limit_{wallet_id}"
    return check_rate_limit(key, limit, timeout)