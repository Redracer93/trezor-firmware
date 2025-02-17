from typing import TYPE_CHECKING

from trezor.crypto import nem

if TYPE_CHECKING:
    from trezor.messages import (
        NEMAggregateModification,
        NEMSignTx,
        NEMTransactionCommon,
    )


async def ask_multisig(msg: NEMSignTx) -> None:
    from ..layout import require_confirm_fee

    assert msg.multisig is not None  # sign_tx
    assert msg.multisig.signer is not None  # sign_tx
    address = nem.compute_address(msg.multisig.signer, msg.transaction.network)
    if msg.cosigning:
        await _require_confirm_address("Cosign transaction for", address)
    else:
        await _require_confirm_address("Initiate transaction for", address)
    await require_confirm_fee("Confirm multisig fee", msg.transaction.fee)


async def ask_aggregate_modification(
    common: NEMTransactionCommon,
    mod: NEMAggregateModification,
    multisig: bool,
) -> None:
    from trezor.enums import NEMModificationType
    from ..layout import require_confirm_final, require_confirm_text

    if not multisig:
        await require_confirm_text("Convert account to multisig account?")

    for m in mod.modifications:
        if m.type == NEMModificationType.CosignatoryModification_Add:
            action = "Add"
        else:
            action = "Remove"
        address = nem.compute_address(m.public_key, common.network)
        await _require_confirm_address(action + " cosignatory", address)

    if mod.relative_change:
        if multisig:
            action = "Modify the number of cosignatories by "
        else:
            action = "Set minimum cosignatories to "
        await require_confirm_text(action + str(mod.relative_change) + "?")

    await require_confirm_final(common.fee)


async def _require_confirm_address(action: str, address: str) -> None:
    from trezor.enums import ButtonRequestType
    from trezor.ui.layouts import confirm_address

    await confirm_address(
        "Confirm address",
        address,
        action,
        "confirm_multisig",
        ButtonRequestType.ConfirmOutput,
    )
