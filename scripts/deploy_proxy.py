from scripts.helpers import deploy_proxy, upgrade
from brownie import Game, GameV2, Contract, config, network, accounts
from web3 import Web3


def deploy_game_and_proxy():
    owner = accounts[0]

    # deploy game V1
    print("\nDeploying GAME V1 ...")
    nft_game = Game.deploy(
        {"from": owner},
        publish_source=config["networks"][network.show_active()].get("publish", False),
        )
    
    print("\nDeploying proxy, proxy admin, ...")
    # deploy proxy
    proxy_admin, proxy_nft_game, proxy = deploy_proxy(owner, nft_game, "Game")
    
    print ("Deploying GAME V2 ...")
    # deploy game V2
    nft_game_V2 = GameV2.deploy(
        {"from": owner},
        publish_source=config["networks"][network.show_active()].get("publish", False),
        )

    # upgrade
    print("\nUpgrading the proxy...")
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


def main():
    deploy_game_and_proxy()
    