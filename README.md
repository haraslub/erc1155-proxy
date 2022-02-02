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

    To reproduced, please see the following lines of code:

    **deploy_proxy.py**

    ```
    from scripts.helpers import deploy_proxy, upgrade
    from brownie import Game, GameV2, Contract, exceptions, config, network, accounts
    from web3 import Web3


    def deploy_game_and_proxy():
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


    def main():
        deploy_game_and_proxy()
    ```

    **helpers.py**

    ```
    from brownie import (
        network, config, Contract,
        TransparentUpgradeableProxy, ProxyAdmin,
    )
    import eth_utils


    NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["hardhat", "development", "ganache"]
    LOCAL_BLOCKCHAIN_ENVIRONMENTS = NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS + [
        "mainnet-fork",
    ]


    def encode_function_data(initializer=None, *args):
        """
        Encodes the function call so we can work with an initializer.

        Args:
            initializer ([brownie.network.contract.ContractTx], optional):
            The initializer function we want to call. Example: 'box.store'.
            Defaults to None.

            args (Any, optional):
            The arguments to pass to the initializer function.

        Returns:
            [bytes]: Return the encoded bytes.
        """
        if len(args) == 0 or not initializer:
            return eth_utils.to_bytes(hexstr="0x") # to return at least some bytes;
        return initializer.encode_input(*args)


    def upgrade(
        account,
        proxy,
        new_implementation_address,
        proxy_admin_contract=None,
        initializer=None,
        *args
        ):
        """
        Update our proxy contract:

        Args:
            account (string, address): the caller account private key
            proxy (string, contract): the proxy contract to be updated
            new_implementation_address (string, address): the address of implementation contract (the new one)
            proxy_admin_contract (string, contract, optional): if admin contract exists
            initializer (string, optional): if initializer exists (to be encoded)
            *args (Any, optional): if *args exists (parameter to be encoded with initializer)
        """
        transaction = None
        if proxy_admin_contract:
            if initializer:
                # encode initiliazer in bytes
                encoded_function_call = encode_function_data(initializer, *args)
                # upgrade the proxy admin contract with encoded initializer
                transaction = proxy_admin_contract.upgradeAndCall(
                    proxy.address,
                    new_implementation_address,
                    encoded_function_call,
                    {"from": account},
                )
            else:
                # upgrade the proxy admin contract WITHOUT encoded initializer
                transaction = proxy_admin_contract.upgrade(
                    proxy.address,
                    new_implementation_address,
                    {"from": account},
                )
        else:
        # if proxy admin does not exists
            if initializer:
                # encode initiliazer in bytes
                encoded_function_call = encode_function_data(initializer, *args)
                transaction = proxy.upgradeToAndCall(
                    new_implementation_address,
                    encoded_function_call,
                    {"from": account},
                )
            else:
                transaction == proxy.upgradeTo(
                    new_implementation_address,
                    {"from": account},
                )
        return transaction


    def deploy_proxy(account, contract_deployed, contract_name="contract", initilizer=None, *args):
        # 1.create proxy admin
        proxy_admin = ProxyAdmin.deploy(
            {"from": account},
            publish_source=config["networks"][network.show_active()].get("publish", False)
            )
        # 2.encode initiazer
        if initilizer:
            encoded_initiliazer = encode_function_data(initilizer, *args)
        else:
            encoded_initiliazer = encode_function_data()
        # 3.create proxy
        proxy = TransparentUpgradeableProxy.deploy(
            contract_deployed.address,
            proxy_admin.address,
            encoded_initiliazer,
            {"from": account, "gas_limit": 1000000},
            publish_source=config["networks"][network.show_active()].get("publish", False)
        )
        # 4. create proxy contract
        proxy_contract = Contract.from_abi(
            contract_name, proxy.address, contract_deployed.abi
        )
        return proxy_admin, proxy_contract, proxy
    ```

    **Game.sol**

    ```
    // SPDX-License-Identifier: MIT

    pragma solidity ^0.8.0;

    import "@openzeppelin/contracts/access/Ownable.sol";
    import "@openzeppelin/contracts/utils/math/SafeMath.sol";
    import "@openzeppelin/contracts/token/ERC1155/presets/ERC1155PresetMinterPauser.sol";

    contract Game is ERC1155PresetMinterPauser, Ownable {

        using SafeMath for uint256;

        uint256 public constant APPLE = 0;
        uint256 public constant PEAR = 1;
        uint256 public constant CHERRY = 2;

        uint256[] public mintedTotal = [0, 0, 0];
        uint256 public mintedPublicly;
        uint256 public maxAvailableForPublicMint = 1000;
        uint256[] public ratesForPublicMint = [0.01 ether, 0.01 ether, 0.01 ether];

        // Mapping from token ID to Users's balances
        mapping(uint256 => mapping(address => uint256)) private Users;

        // variable related to burning item in order to mint another item
        uint256 public fruitToBurn = PEAR;
        uint256 public fruitToMint = CHERRY;

        constructor() ERC1155PresetMinterPauser("https://address.io/{id}.json")
        {
            _setupRole(DEFAULT_ADMIN_ROLE, _msgSender());
        }

        function mint(address user, uint256 id, uint256 amount) public {
            require(hasRole(MINTER_ROLE, _msgSender()), "ERC1155PresetMinterPauser: must have minter role to mint");
            require(0 <= id && id <= mintedTotal.length, "Fruit does not exists!");
            mintedTotal[id] = mintedTotal[id].add(amount);
            Users[id][user] = Users[id][user].add(amount);
            _mint(user, id, amount, "");
        }

        // withdraw ETH sent to the contract (during public Mint for instance)
        function withdraw() public {
            require(hasRole(DEFAULT_ADMIN_ROLE, _msgSender()), "ERC1155PresetMinterPauser: must have minter role to mint");
            require(address(this).balance > 0, "Balance is zero, cannot withdraw");
            payable(owner()).transfer(address(this).balance);
        }

        // burn allowed fruit in order to try luck in getting different fruit
        function burnToGainFruit(uint256 id, uint256 amount) public {
            require(0 <= id && id <= mintedTotal.length, "Fruit does not exists!");
            require(id == fruitToBurn, "This fruit cannot be burnt!");
            address user = msg.sender;
            for (uint i=1; i <= amount; i++) {
                require(Users[id][user] > 0, "There is nothing to burn");
                Users[id][user] = Users[id][user].sub(1);
                _burn(user, id, 1);
            }
        }

    }
    ```

    **GameV2.sol** (= Game.sol extended by `setBurnToGainParameters` function)

    ```
    // SPDX-License-Identifier: MIT

    pragma solidity ^0.8.0;

    import "@openzeppelin/contracts/access/Ownable.sol";
    import "@openzeppelin/contracts/utils/math/SafeMath.sol";
    import "@openzeppelin/contracts/token/ERC1155/presets/ERC1155PresetMinterPauser.sol";

    contract GameV2 is ERC1155PresetMinterPauser, Ownable {

        using SafeMath for uint256;

        uint256 public constant APPLE = 0;
        uint256 public constant PEAR = 1;
        uint256 public constant CHERRY = 2;

        uint256[] public mintedTotal = [0, 0, 0];
        uint256 public mintedPublicly;
        uint256 public maxAvailableForPublicMint = 1000;
        uint256[] public ratesForPublicMint = [0.01 ether, 0.01 ether, 0.01 ether];

        // Mapping from token ID to Users's balances
        mapping(uint256 => mapping(address => uint256)) private Users;

        // variable related to burning item in order to mint another item
        uint256 public fruitToBurn = PEAR;
        uint256 public fruitToMint = CHERRY;

        constructor() ERC1155PresetMinterPauser("https://address.io/{id}.json")
        {
            _setupRole(DEFAULT_ADMIN_ROLE, _msgSender());
        }

        function mint(address user, uint256 id, uint256 amount) public {
            require(hasRole(MINTER_ROLE, _msgSender()), "ERC1155PresetMinterPauser: must have minter role to mint");
            require(0 <= id && id <= mintedTotal.length, "Fruit does not exists!");
            mintedTotal[id] = mintedTotal[id].add(amount);
            Users[id][user] = Users[id][user].add(amount);
            _mint(user, id, amount, "");
        }

        // withdraw ETH sent to the contract (during public Mint for instance)
        function withdraw() public {
            require(hasRole(DEFAULT_ADMIN_ROLE, _msgSender()), "ERC1155PresetMinterPauser: must have minter role to mint");
            require(address(this).balance > 0, "Balance is zero, cannot withdraw");
            payable(owner()).transfer(address(this).balance);
        }

        // burn allowed fruit in order to try luck in getting different fruit
        function burnToGainFruit(uint256 id, uint256 amount) public {
            require(0 <= id && id <= mintedTotal.length, "Fruit does not exists!");
            require(id == fruitToBurn, "This fruit cannot be burnt!");
            address user = msg.sender;
            for (uint i=1; i <= amount; i++) {
                require(Users[id][user] > 0, "There is nothing to burn");
                Users[id][user] = Users[id][user].sub(1);
                _burn(user, id, 1);
            }
        }

        function setBurnToGainParameters(uint256 _fruitToBurn, uint256 _fruitToMint)
        external returns (bool) {
            require(hasRole(DEFAULT_ADMIN_ROLE, _msgSender()), "ERC1155PresetMinterPauser: must have admin role to change variables");
            require(0 <= _fruitToBurn && _fruitToBurn < mintedTotal.length, "Fruit to burn does not exists!");
            require(0 <= _fruitToMint && _fruitToMint < mintedTotal.length, "Fruit to mint does not exists!");
            fruitToBurn = _fruitToBurn;
            fruitToMint = _fruitToMint;
            return true;
        }

    }
    ```
