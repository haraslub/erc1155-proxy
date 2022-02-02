I want to upgrade my ERC1155 game from Game.sol to GameV2.sol using Openzeppelin's contracts ProxyAdmin and TransparentUpgradeableProxy. I have implemented ERC1155PresetMinterPauser to Game/GameV2 contracts in order to be able set roles, change game parameters etc. afterwards.

During testing the functionality of the proxy by using function `setBurnToGainParameters` from GameV2.sol via proxy (details related to all steps made can be seen in deploy_proxy.py below), I get:

```
>>> proxy_nft_game_V2.setBurnToGainParameters(0, 1, {"from": owner})
Transaction sent: 0x448645520a6f3db29beb700a17cad884cdcb3e771797af0653f9cd81b4e7189e
Gas price: 0.0 gwei   Gas limit: 12000000   Nonce: 5
Transaction confirmed (ERC1155PresetMinterPauser: must have admin role to change variables)   Block: 6   Gas used: 25756 (0.21%)
```

So, I tried to check, if owner adress (me) has a admin role, i.e. `0x0000000000000000000000000000000000000000`:

```
>>> nft_game_V2.hasRole(ADMIN_ROLE, owner)
True
>>> proxy_nft_game_V2.hasRole(ADMIN_ROLE, owner)
False
```

Based on https://docs.openzeppelin.com/upgrades-plugins/1.x/proxies#proxy-forwarding

> A very important thing to note is that the code makes use of the EVM’s delegatecall opcode which executes the callee’s code in the context of the caller’s state. That is, the logic contract controls the proxy’s state and the logic contract’s state is meaningless. Thus, the proxy doesn’t only forward transactions to and from the logic contract, but also represents the pair’s state. The state is in the proxy and the logic is in the particular implementation that the proxy points to.

I guess that the admin and any other variables defined in the GameV2 are actually not stored in the proxy contract. Question is what is the proper way to set them in the proxy and be able to call all functions required roles (admin's, minter, etc.)?

Could anyone help me, please?
