import httpx
import solders
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from solders import message
from solders.keypair import Keypair

from .metadata import *
from .solana_fm import get_owner_token_accounts


class SolClient:
    ENDPOINT = 'https://api.mainnet-beta.solana.com/'
    WEBSOCKET_ENDPOINT = 'wss://api.mainnet-beta.solana.com/'
    _C = Client(ENDPOINT)
    _W_C = Client(WEBSOCKET_ENDPOINT)

    def __init__(
            self,
            endpoint: str = 'https://api.mainnet-beta.solana.com/',
            websocket_endpoint: str = 'wss://api.mainnet-beta.solana.com/',
    ):
        self.ENDPOINT = endpoint
        self.WEBSOCKET_ENDPOINT = endpoint
        self._C = Client(endpoint)
        self._W_C = Client(websocket_endpoint)

    @staticmethod
    def send_tx(tx: str, sender: Keypair) -> dict:
        """
        Send (perform) transaction.
        """
        raw_tx = solders.transaction.VersionedTransaction.from_bytes(
            base64.b64decode(tx)
        )
        signed_txn = sender.sign_message(message.to_bytes_versioned(raw_tx.message))
        s_signed_txn = solders.transaction.VersionedTransaction.populate(
            raw_tx.message, [signed_txn]
        )
        encoded_tx = base64.b64encode(bytes(s_signed_txn)).decode("utf-8")

        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                encoded_tx,
                {
                    "skipPreflight": True,
                    "preflightCommitment": "finalized",
                    "encoding": "base64",
                    "maxRetries": None,
                    "minContextSlot": None,
                },
            ],
        }

        response = httpx.post(
            "https://api.mainnet-beta.solana.com",
            headers=headers,
            json=data,
        )
        return response.json()

    async def get_sol_balance(self, account: str) -> float:
        """
        Returns SOL account balance.
        """
        client = self._C
        account = Pubkey.from_string(account)
        balance = client.get_balance(account)
        balance = json.loads(balance.to_json())
        try:
            balance = round(balance['result']['value'] / 1000000000, 5)
            return balance
        except:
            raise Exception(f'sol.get_sol_balance error: {balance}')

    def get_token_portfolio(self, account: str) -> list[list[str, str, float]]:
        """
        Returns account token portfolio.
        :return: [[<token1_address>, <token1_symbol>, <token1_account_balance>], ...]
        """
        client = self._C
        tokens = get_owner_token_accounts(account)
        metadata_accounts = []
        for token in tokens:
            m = get_metadata_account(token[0])
            metadata_accounts.append(m)
        accounts = json.loads(client.get_multiple_accounts(metadata_accounts).to_json())['result']['value']
        res = []
        for acc in accounts:
            data = base64.b64decode(acc['data'][0])
            metadata = unpack_metadata_account(data)
            balance = 0
            for i in tokens:
                if i[0] == metadata['mint'].decode('utf-8'):
                    balance = i[1]
            res.append([metadata['mint'].decode('utf-8'), metadata['data']['symbol'], balance])
        return res

    def get_token_symbol(self, token_address: str) -> str:
        """
        Return token symbol.
        """
        client = self._C
        account = get_metadata_account(token_address)
        account = client.get_account_info(account)
        if not account.value:
            raise Exception(f'error in sol.get_token_symbol: incorrect token_address')
        try:
            account = json.loads(account.to_json())
            account = account['result']['value']
            data = base64.b64decode(account['data'][0])
            metadata = unpack_metadata_account(data)
            return metadata['data']['symbol']
        except:
            raise Exception(f'error in sol.get_token_symbol: {account}')

    def get_token_balance(self, account: str, token_address: str) -> float:
        """
        Returns account token balance.
        """
        client = self._C
        token_address = Pubkey.from_string(token_address)
        account = Pubkey.from_string(account)
        opts = TokenAccountOpts(mint=token_address)
        token_accounts = client.get_token_accounts_by_owner(account, opts)
        token_accounts = json.loads(token_accounts.to_json())
        try:
            if token_accounts['result']['value']:
                token_account = Pubkey.from_string(token_accounts['result']['value'][0]['pubkey'])
                balance = client.get_token_account_balance(token_account)
                return balance.value.ui_amount
            else:
                return 0
        except:
            raise Exception(f'sol.get_token_balance error: {token_accounts}')

    def get_token_decimals(self, token_address: str) -> int:
        """
        Returns token decimals.
        """
        client = self._C
        info = client.get_account_info_json_parsed(Pubkey.from_string(token_address))
        try:
            return info.value.data.parsed['info']['decimals']
        except:
            raise Exception(f'sol.get_token_decimals error: {info.to_json()}')
