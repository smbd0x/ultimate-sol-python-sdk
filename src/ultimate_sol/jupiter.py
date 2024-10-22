import base64

import httpx
from solders import message
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction


class Jupiter:
    ENDPOINT_APIS_URL = {
        "QUOTE": "https://quote-api.jup.ag/v6/quote?",
        "SWAP": "https://quote-api.jup.ag/v6/swap",
        "OPEN_ORDER": "https://jup.ag/api/limit/v1/createOrder",
        "CANCEL_ORDERS": "https://jup.ag/api/limit/v1/cancelOrders",
        "QUERY_OPEN_ORDERS": "https://jup.ag/api/limit/v1/openOrders?wallet=",
        "QUERY_ORDER_HISTORY": "https://jup.ag/api/limit/v1/orderHistory",
        "QUERY_TRADE_HISTORY": "https://jup.ag/api/limit/v1/tradeHistory"
    }

    def __init__(
            self,
            keypair: Keypair,
            quote_api_url: str = "https://quote-api.jup.ag/v6/quote?",
            swap_api_url: str = "https://quote-api.jup.ag/v6/swap",
            open_order_api_url: str = "https://jup.ag/api/limit/v1/createOrder",
            cancel_orders_api_url: str = "https://jup.ag/api/limit/v1/cancelOrders",
            query_open_orders_api_url: str = "https://jup.ag/api/limit/v1/openOrders?wallet=",
            query_order_history_api_url: str = "https://jup.ag/api/limit/v1/orderHistory",
            query_trade_history_api_url: str = "https://jup.ag/api/limit/v1/tradeHistory",
    ):
        self.keypair = keypair

        self.ENDPOINT_APIS_URL["QUOTE"] = quote_api_url
        self.ENDPOINT_APIS_URL["SWAP"] = swap_api_url
        self.ENDPOINT_APIS_URL["OPEN_ORDER"] = open_order_api_url
        self.ENDPOINT_APIS_URL["CANCEL_ORDERS"] = cancel_orders_api_url
        self.ENDPOINT_APIS_URL["QUERY_OPEN_ORDERS"] = query_open_orders_api_url
        self.ENDPOINT_APIS_URL["QUERY_ORDER_HISTORY"] = query_order_history_api_url
        self.ENDPOINT_APIS_URL["QUERY_TRADE_HISTORY"] = query_trade_history_api_url

    def quote(
            self,
            input_mint: str,
            output_mint: str,
            amount: int,
            slippage_bps: int = None,
            swap_mode: str = "ExactIn",
            only_direct_routes: bool = False,
            as_legacy_transaction: bool = False,
            exclude_dexes: list = None,
            max_accounts: int = None,
            platform_fee_bps: int = None
    ) -> dict:
        """
        Get the best swap route for a token trade pair sorted by largest output token amount from
        https://quote-api.jup.ag/v6/quote. Docs: https://station.jup.ag/api-v6/get-quote.
        """

        quote_url = self.ENDPOINT_APIS_URL[
                        'QUOTE'] + "inputMint=" + input_mint + "&outputMint=" + output_mint + "&amount=" + str(
            amount) + "&swapMode=" + swap_mode + "&onlyDirectRoutes=" + str(
            only_direct_routes).lower() + "&asLegacyTransaction=" + str(as_legacy_transaction).lower()
        if slippage_bps:
            quote_url += "&slippageBps=" + str(slippage_bps)
        if exclude_dexes:
            quote_url += "&excludeDexes=" + ','.join(exclude_dexes)
        if max_accounts:
            quote_url += "&maxAccounts=" + str(max_accounts)
        if platform_fee_bps:
            quote_url += "&plateformFeeBps=" + str(platform_fee_bps)

        quote_response = httpx.get(url=quote_url)
        quote_response = quote_response.json()
        return quote_response

    def swap(
            self,
            input_mint: str,
            output_mint: str,
            amount: int = 0,
            quote_response: str = None,
            wrap_unwrap_sol: bool = True,
            slippage_bps: int = 1,
            swap_mode: str = "ExactIn",
            prioritization_fee_lamports: int = None,
            only_direct_routes: bool = False,
            as_legacy_transaction: bool = False,
            exclude_dexes: list = None,
            max_accounts: int = None,
            platform_fee_bps: int = None
    ) -> str:
        """
        Perform a swap. Docs: https://station.jup.ag/api-v6/post-swap.
        """

        if quote_response is None:
            quote_response = self.quote(
                input_mint=input_mint,
                output_mint=output_mint,
                amount=amount,
                slippage_bps=slippage_bps,
                swap_mode=swap_mode,
                only_direct_routes=only_direct_routes,
                as_legacy_transaction=as_legacy_transaction,
                exclude_dexes=exclude_dexes,
                max_accounts=max_accounts,
                platform_fee_bps=platform_fee_bps
            )

        transaction_parameters = {
            "userPublicKey": self.keypair.pubkey().__str__(),
            "wrapAndUnwrapSol": wrap_unwrap_sol,
            "quoteResponse": quote_response,
        }
        if prioritization_fee_lamports:
            transaction_parameters.update({"prioritizationFeeLamports": prioritization_fee_lamports})

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        transaction_data = httpx.post(url=self.ENDPOINT_APIS_URL['SWAP'], headers=headers, json=transaction_parameters)
        transaction_data = transaction_data.json()
        try:
            return transaction_data['swapTransaction']
        except:
            raise Exception(transaction_data['error'])

    def open_order(
            self,
            input_mint: str,
            output_mint: str,
            in_amount: int = 0,
            out_amount: int = 0,
            expired_at: int = None
    ) -> dict:
        """
        Open an order. Docs: https://station.jup.ag/docs/limit-order/limit-order.
        """

        keypair = Keypair()
        transaction_parameters = {
            "owner": self.keypair.pubkey().__str__(),
            "inputMint": input_mint,
            "outputMint": output_mint,
            "outAmount": out_amount,
            "inAmount": in_amount,
            "base": keypair.pubkey().__str__()
        }
        if expired_at:
            transaction_parameters['expiredAt'] = expired_at

        transaction_data = httpx.post(url=self.ENDPOINT_APIS_URL['OPEN_ORDER'], json=transaction_parameters)
        try:
            transaction_data = transaction_data.json()['tx']
        except:
            raise Exception(transaction_data.json()['error'])
        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
        signature2 = keypair.sign_message(message.to_bytes_versioned(raw_transaction.message))
        return {"transaction_data": transaction_data, "signature2": signature2}


def get_tokens_list(
        list_type: str = "strict",
        banned_tokens: bool = False
) -> dict:
    """
    Returns token list.
    Docs: https://station.jup.ag/docs/token-list/token-list-api
    """

    tokens_list_url = "https://token.jup.ag/" + list_type
    if banned_tokens is True:
        tokens_list_url += "?includeBanned=true"

    tokens_list = httpx.get(tokens_list_url)
    tokens_list = tokens_list.json()
    return tokens_list


def get_all_tickers(
) -> dict:
    """
    Returns all tickers (cached for every 2-5 mins) from https://stats.jup.ag/coingecko/tickers.
    Docs: https://station.jup.ag/docs/additional-topics/displaying-jup-stats
    """

    all_tickers_list = httpx.get("https://stats.jup.ag/coingecko/tickers")
    return all_tickers_list.json()


def get_token_price(
        input_mint: str,
        output_mint: str = None,
) -> tuple:
    """
    Return token price (works with pump.fun tokens).
    Docs: https://station.jup.ag/docs/apis/price-api

    :return: tuple with input_mint and price in output_mint values (in USDC if None)
    """
    token_prices_url = "https://price.jup.ag/v6/price?ids=" + input_mint
    if output_mint:
        token_prices_url += "&vsToken=" + output_mint

    token_prices = httpx.get(token_prices_url)
    try:
        price = float(token_prices.json()['data'][input_mint]['price'])
        return input_mint, price
    except:
        return input_mint, 0


def get_token_info(token_address: str) -> dict | None:
    """
    Returns info about token, like decimals, symbol, logo and the like (works with pump.fun tokens).\n
    Docs: https://station.jup.ag/docs/token-list/token-list-api
    """

    result = httpx.get(f'https://tokens.jup.ag/token/{token_address}').json()
    if result:
        return result
    return None
