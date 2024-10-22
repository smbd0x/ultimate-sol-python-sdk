import base64
import json
import struct
from enum import IntEnum

import base58
from construct import Bytes, Int8ul
from construct import Struct as cStruct
from solders.pubkey import Pubkey

MAX_NAME_LENGTH = 32
MAX_SYMBOL_LENGTH = 10
MAX_URI_LENGTH = 200
MAX_CREATOR_LENGTH = 34
MAX_CREATOR_LIMIT = 5


class InstructionType(IntEnum):
    CREATE_METADATA = 0
    UPDATE_METADATA = 1


METADATA_PROGRAM_ID = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')


def get_metadata_account(mint_key):
    return Pubkey.find_program_address(
        [b'metadata', bytes(METADATA_PROGRAM_ID), bytes(Pubkey.from_string(mint_key))],
        METADATA_PROGRAM_ID
    )[0]


def get_edition(mint_key):
    return Pubkey.find_program_address(
        [b'metadata', bytes(METADATA_PROGRAM_ID), bytes(Pubkey.from_string(mint_key)), b"edition"],
        METADATA_PROGRAM_ID
    )[0]


def _get_data_buffer(name, symbol, uri, fee, creators, verified=None, share=None):
    if isinstance(share, list):
        assert (len(share) == len(creators))
    if isinstance(verified, list):
        assert (len(verified) == len(creators))
    args = [
        len(name),
        *list(name.encode()),
        len(symbol),
        *list(symbol.encode()),
        len(uri),
        *list(uri.encode()),
        fee,
    ]

    byte_fmt = "<"
    byte_fmt += "I" + "B" * len(name)
    byte_fmt += "I" + "B" * len(symbol)
    byte_fmt += "I" + "B" * len(uri)
    byte_fmt += "h"
    byte_fmt += "B"
    if creators:
        args.append(1)
        byte_fmt += "I"
        args.append(len(creators))
        for i, creator in enumerate(creators):
            byte_fmt += "B" * 32 + "B" + "B"
            args.extend(list(base58.b58decode(creator)))
            if isinstance(verified, list):
                args.append(verified[i])
            else:
                args.append(1)
            if isinstance(share, list):
                args.append(share[i])
            else:
                args.append(100)
    else:
        args.append(0)
    buffer = struct.pack(byte_fmt, *args)
    return buffer


def unpack_metadata_account(data):
    assert (data[0] == 4)
    i = 1
    source_account = base58.b58encode(bytes(struct.unpack('<' + "B" * 32, data[i:i + 32])))
    i += 32
    mint_account = base58.b58encode(bytes(struct.unpack('<' + "B" * 32, data[i:i + 32])))
    i += 32
    name_len = struct.unpack('<I', data[i:i + 4])[0]
    i += 4
    name = struct.unpack('<' + "B" * name_len, data[i:i + name_len])
    i += name_len
    symbol_len = struct.unpack('<I', data[i:i + 4])[0]
    i += 4
    symbol = struct.unpack('<' + "B" * symbol_len, data[i:i + symbol_len])
    i += symbol_len
    uri_len = struct.unpack('<I', data[i:i + 4])[0]
    i += 4
    uri = struct.unpack('<' + "B" * uri_len, data[i:i + uri_len])
    i += uri_len
    fee = struct.unpack('<h', data[i:i + 2])[0]
    i += 2
    has_creator = data[i]
    i += 1
    creators = []
    verified = []
    share = []
    if has_creator:
        creator_len = struct.unpack('<I', data[i:i + 4])[0]
        i += 4
        for _ in range(creator_len):
            creator = base58.b58encode(bytes(struct.unpack('<' + "B" * 32, data[i:i + 32])))
            creators.append(creator)
            i += 32
            verified.append(data[i])
            i += 1
            share.append(data[i])
            i += 1
    primary_sale_happened = bool(data[i])
    i += 1
    is_mutable = bool(data[i])
    metadata = {
        "update_authority": source_account,
        "mint": mint_account,
        "data": {
            "name": bytes(name).decode("utf-8").strip("\x00"),
            "symbol": bytes(symbol).decode("utf-8").strip("\x00"),
            "uri": bytes(uri).decode("utf-8").strip("\x00"),
            "seller_fee_basis_points": fee,
            "creators": creators,
            "verified": verified,
            "share": share,
        },
        "primary_sale_happened": primary_sale_happened,
        "is_mutable": is_mutable,
    }
    return metadata


def get_metadata(client, mint_key) -> dict:
    metadata_account = get_metadata_account(mint_key)
    data = json.loads(client.get_account_info(metadata_account).to_json())['result']['value']['data'][0]
    data = base64.b64decode(data)
    metadata = unpack_metadata_account(data)
    return metadata


def update_metadata_instruction_data(name, symbol, uri, fee, creators, verified, share):
    _data = bytes([1]) + _get_data_buffer(name, symbol, uri, fee, creators, verified, share) + bytes([0, 0])
    instruction_layout = cStruct(
        "instruction_type" / Int8ul,
        "args" / Bytes(len(_data)),
    )
    return instruction_layout.build(
        dict(
            instruction_type=InstructionType.UPDATE_METADATA,
            args=_data,
        )
    )

