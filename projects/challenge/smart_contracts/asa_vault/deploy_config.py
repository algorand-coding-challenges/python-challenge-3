import logging

import algokit_utils
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from algosdk import transaction
from algosdk.atomic_transaction_composer import TransactionWithSigner

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: algokit_utils.ApplicationSpecification,
    deployer: algokit_utils.Account,
) -> None:
    from smart_contracts.artifacts.asa_vault.client import (
        AsaVaultClient,
    )

    # create the ASA to deposit in the vault
    sp = algod_client.suggested_params()

    asa_create_txn = transaction.AssetConfigTxn(
        sender=deployer.address,
        sp=sp,
        total=10,
        decimals=0,
        unit_name="SRO",
        asset_name="Super RARE Oranges",
        strict_empty_address_check=False,
    )

    stxn = asa_create_txn.sign(deployer.private_key)    
    txid = algod_client.send_transaction(stxn)
    results = transaction.wait_for_confirmation(algod_client, txid, 4)

    created_asset = results["asset-index"]
    print(f"The Super RARE Oranges is created and has asset id: {created_asset}")

    # Instantiate the app client
    app_client = AsaVaultClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )

    # Deploy the vault smart contract and assign the created ASA to it
    response = app_client.create_create_application(asset=created_asset)
    print(f"Created app with app id: {response.tx_info['application-index']}")

    # Send the mbr amount to the vault and call the opt in method so that the vault can receive the ASA
    mbr_pay = transaction.PaymentTxn(
        sender=deployer.address,
        sp=sp,
        receiver=app_client.app_address,
        amt= 200_000,
    )

    sp = algod_client.suggested_params()
    sp.fee = 2000
    sp.flat_fee = True

    app_client.opt_in_to_asset(
        mbr_pay=TransactionWithSigner(mbr_pay, deployer.signer), 
        transaction_parameters=algokit_utils.TransactionParameters(
            foreign_assets=[created_asset],
            suggested_params=sp
    ))

    # Deposit the ASA into the vault
    deposit_txn = transaction.AssetTransferTxn(
        sender=deployer.address,
        sp=sp,
        receiver=app_client.app_address,
        amt= 1,
        index=created_asset,
    )

    app_client.deposit_asa(deposit_txn=TransactionWithSigner(deposit_txn, deployer.signer))

    # Check the balance of the vault
    response = app_client.get_asa_balance()
    print(f"The Vault holds {response.return_value} Super RARE Oranges")

    app_client.deposit_asa(deposit_txn=TransactionWithSigner(deposit_txn, deployer.signer))

    response = app_client.get_asa_balance()
    print(f"The Vault holds {response.return_value} Super RARE Oranges")

    sp = algod_client.suggested_params()
    sp.fee = 2000
    sp.flat_fee = True

    # Withdraw the ASA from the vault
    app_client.withdraw_asa(asset=created_asset, transaction_parameters= algokit_utils.TransactionParameters(
        suggested_params=sp
    ))

    response = app_client.get_asa_balance()
    print(f"The Vault holds {response.return_value} Super RARE Oranges")

