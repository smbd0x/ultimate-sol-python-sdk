import httpx


def get_owner_token_accounts(account: str) -> list:
    """
    Returns a list with addresses and balances of all account tokens.
    Docs: https://docs.solana.fm/reference/get_tokens_owned_by_account_handler
    """
    headers = {"accept": "application/json"}
    tokens = httpx.get(f"https://api.solana.fm/v1/addresses/{account}/tokens", headers=headers)
    if tokens.status_code == 200:
        tokens = tokens.json()['tokens']
        res = []
        for token in tokens:
            if tokens[token]['balance']:
                res.append([token, tokens[token]['balance'], 4])
        return res
    else:
        raise Exception(f'solana_fm.get_owner_token_accounts error: {tokens.json()}')
