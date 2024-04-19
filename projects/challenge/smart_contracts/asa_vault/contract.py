from algopy import ARC4Contract, arc4, UInt64, Asset, gtxn, itxn, Txn, Global,subroutine

class AsaVault(ARC4Contract):
    asset_id: UInt64
    asa_balance: UInt64

    # create the app and configure what ASA this vault will hold
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def create_application(self, asset: Asset) -> None:
        self.asset_id = asset.id
        self.asa_balance = UInt64(0)

    @subroutine
    def authorize_creator(self) -> None:
        assert Txn.sender == Global.creator_address

    @arc4.abimethod
    def opt_in_to_asset(self, mbr_pay: gtxn.PaymentTransaction) -> None:
        self.authorize_creator()
        assert not Global.current_application_address.is_opted_in(Asset(self.asset_id))

        assert mbr_pay.receiver == Global.current_application_address
        assert mbr_pay.amount == Global.min_balance + Global.asset_opt_in_min_balance

        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver=Global.current_application_address,
            fee=0
        ).submit()
        
    @arc4.abimethod
    def deposit_asa(self, deposit_txn: gtxn.AssetTransferTransaction)-> None: 
        self.authorize_creator()
        assert deposit_txn.asset_receiver == Global.current_application_address
        assert deposit_txn.asset_amount > 0

        self.asa_balance += deposit_txn.asset_amount

    @arc4.abimethod
    def withdraw_asa(self, asset: Asset) -> None:
        self.authorize_creator()

        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver=Global.creator_address,
            asset_amount=0,
            asset_close_to=Global.creator_address,
            fee=0,
        ).submit()

        self.asa_balance = UInt64(0)

    @arc4.abimethod(readonly=True)
    def get_asa_balance(self) -> UInt64:
        return self.asa_balance
        