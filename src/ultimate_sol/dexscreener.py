import httpx


def get_token_profile(token_address: str) -> dict | None:
    """
    Returns token profile (if exist) from dexscreener with name, symbol, price, volume, etc.\n
    Docs: https://docs.dexscreener.com/api/reference
    """
    url = f'https://api.dexscreener.com/latest/dex/tokens/{token_address}'
    response = httpx.get(url)
    if response.status_code == 200:
        response = response.json()
        if response.get('pairs'):
            for pair in response['pairs']:
                if pair['quoteToken']['address'] == 'So11111111111111111111111111111111111111112':
                    return pair
        else:
            return None
    else:
        raise Exception(f'dexscreener.get_token_profile() error: {response.json()}')
