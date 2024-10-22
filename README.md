

<div align="center">
<h1>Ultimate-Sol Python SDK</h1>
<img src="https://github.com/smbd0x/ultimate-sol-python-sdk/blob/master/images/logo-banner.png?raw=true" width="30%" height="30%">
</div>

<p align="center">
    <img src="https://img.shields.io/github/stars/smbd0x/ultimate-sol-python-sdk">
    <img src="https://img.shields.io/github/forks/smbd0x/ultimate-sol-python-sdk">
    <br>
    <img src="https://img.shields.io/github/issues/smbd0x/ultimate-sol-python-sdk">
    <img src="https://img.shields.io/github/issues-closed/smbd0x/ultimate-sol-python-sdk">
    <br>
    <img src="https://img.shields.io/github/languages/top/smbd0x/ultimate-sol-python-sdk">
    <img src="https://img.shields.io/github/last-commit/smbd0x/ultimate-sol-python-sdk">
    <br>
</p>

## What is this? ##
This library contains a set of functions for interacting with Solana blockchain, as well as some third-party APIs such as Jupiter, DexScreener, etc.

## Quick Guide ##
### Installation ###
To install the library, enter command:

    pip install ultimate_sol


----------


### Quick start ###


Using the library is as simple and convenient as possible:


To interact directly with Solana blockchain, use `ultimate_sol.sol.SolClient` class:
    
    from ultimate_sol.sol import SolClient

    client = SolClient()
    account_address = '...'

    account_balance = client.get_sol_balance(account_address)

To interact with Jupiter API, use `ultimate_sol.jupiter.Jupiter` class:

    from ultimate_sol.jupiter import Jupiter
    from solders.keypair import Keypair
    
    secret_key = '...'
    keypair = Keypair.from_base58_string(secret_key)
    jupiter = Jupiter(keypair)

    quote = jupiter.quote(
                        input_mint='...',
                        output_mint='...',
                        amount=0,
                        ...
    )

### Perform and send a swap ###
To perform a swap and send it to blockchain, use this code:
    
    from ultimate_sol.sol import SolClient
    from ultimate_sol.jupiter import Jupiter
    from solders.keypair import Keypair

    secret_key = '...'
    keypair = Keypair.from_base58_string(secret_key)

    client = SolClient()
    jupiter = Jupiter(keypair)

    
    swap = jupiter.swap(
                        input_mint='...',
                        output_mint='...',
                        amount=0,
                        ...
    )
    tx_res = client.send_tx(swap, keypair)

### Get token info ###
To get info about a token, such as symbol or decimals, you can use the following code:
    
    from ultimate_sol.jupiter import get_token_info

    # Returns info about token, like decimals, symbol, logo and the like (works with pump.fun tokens).
    info = get_token_info('...')

Also, you can use `ultimate_sol.metadata.get_metadata` function. It might be faster than `jupiter.get_token_info` if you use a custom Solana Node.
    
    from ultimate_sol.sol import SolClient
    from ultimate_sol.metadata import get_metadata

    client = SolClient()
    info = get_metadata(client, '...')

### Other functions ###
You can also use this library to interact with some other APIs, such as DexScreener or SolanaFM. Example:

    from ultimate_sol.dexscreener import get_token_profile
    
    # Returns token profile (if exist) from dexscreener with name, symbol, price, volume, etc.
    token_profile = get_token_profile('...')  


----------


## Developer ##
My GitHub: [link](https://github.com/smbd0x) 