from scripts.helpers import deploy_proxy, upgrade
from brownie import Game, GameV2, Contract, exceptions, config, network, accounts
from web3 import Web3


def test_proxy_upgrades():
    owner = accounts[0]

    # deploy game V1
    nft_game = Game.deploy(
        {"from": owner},
        publish_source=config["networks"][network.show_active()].get("publish", False),
        )
    
    # deploy proxy
    proxy_admin, proxy_nft_game, proxy = deploy_proxy(owner, nft_game, "Game")
    
    # deploy game V2
    nft_game_V2 = GameV2.deploy(
        {"from": owner},
        publish_source=config["networks"][network.show_active()].get("publish", False),
        )

    # upgrade
    upgrade_nft_game = upgrade(
        owner,
        proxy,
        nft_game_V2.address,
        proxy_admin_contract = proxy_admin,
        initializer=None,
    )
    upgrade_nft_game.wait(1)

    # get proxy of game B2
    proxy_nft_game_V2 = Contract.from_abi(
        "GameV2", proxy.address, GameV2.abi,
    )

    # set the new parameters
    proxy_nft_game_V2.setBurnToGainParameters(0, 1, {"from": owner})

    # get original burn to gain parameters
    # fruit_to_burn_original = proxy_nft_game_V2.fruitToBurn()
    # fruit_to_mint_original = proxy_nft_game_V2.fruitToMint()

    # print("Extracted original burn value: {}".format(fruit_to_burn_original))
    # print("Extracted original mint value: {}".format(fruit_to_mint_original))

    # set new parameters / set role
    # proxy_nft_game_V2.grantRole(DEFAULT_ADMIN_ROLE, proxy_nft_game_V2.address, {"from": owner})
    