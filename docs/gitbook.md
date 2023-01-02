
## General
    - What is a decentralized fiat On and Off Ramp?

        Fiat on and off ramp refers to how users convert their traditional fiat to crypto, and how they convert their crypto back to fiat, crypto in this sense can be tokens, tokenzied assets, stablecoins, etc

        In the past, service that provide this services are usually by a central or single entity making it a fully centralized service mainly offered by exchanges.

        In a decentralized design, on and off ramp happens through a distributed network of users


    - What is Unique about Cowry Protocol?
    - Who can Use cowry Protocol?
        - By design the protocol will have two categories of users;
        - Independent Fiat Providers(IFP).

            - These are Addresses authorized to hold Fiat in Their bank Account, these addresses have gone through the IFP Onboarding process and have staked a certain amount of token with the protocol. Any address can become an IFP and also an IFP can also use the protocol for their deposit and withdrawal of stablecoin. IFPs are the address that will be charge with managing the DAO, IFPs are the ones that decide how the DAO is been govern through voting and other mechanisms. Businesses that want to use the protocol for deposits and withdrawals should always have an address as an IFP which also gives them a say on how the protocol is governed.

        - Other Users.

            - These are all other sets of users who want to use the protocol for deposits and withdrawals, anyone can be among them with no obligation to the protocol than Withdrawals and Deposits of the protocol stablecoin. Other users might also include businesses that interact with the protocol via API provided.

    - What are the Benefits of Using Cowry protocol?
    * How to use Cowry Protocol
        - All users of cowry protocol can access the protocol through using stellar base wallet extensions like [ALBADO](https://albedo.link/), [Freighter](https://www.freighter.app/) via the web app found here
    - Fees for Using the protocol?
        - For deposit and withdrawal, cowry uses a tier fee structure, see our Fee page for more details
    - Who is an Independent Fiat Provider on Cowry Protocol?
        - An Independent Fiat Provider or IFP are Addresses authorized to hold Fiat in Their bank Account, these addresses have gone through the IFP Onboarding process and have staked a certain amount of token with the protocol. Any address can become an IFP and also an IFP can also use the protocol for their deposit and withdrawal of stablecoin. An IFP play a major role in providing fiat liquidity to the protocol. IFPs are the address that will be charge with managing the DAO, IFPs are the ones that decide how the DAO is been govern through voting and other mechanisms. Businesses that want to use the protocol for deposits and withdrawals should always have an address as an IFP which also gives them a say on how the protocol is governed. 

    - Who is a Signer on Cowry Protocol?
        - Signers on the Cowry Protocol are the addresses that signs transaction on the protocol account(mainly the staking address), the signers will start out as the core developers of the protocol overtime other IFPs can apply to join and become signers of the protocol
    - How is my Key Managed?
        - Cowry Protocol does not manage user's key, we use wallet connect protocol for signing transactions which put you(the users) in charge of your key all the time.
    - How is cowry Dao governed?
        - Cowry protocol Dao will start out as a Developer based DAO, we plan to grow the Dao signers and add more signers to the protocol as we progress
    - What fiat currencies are supported ?
        - We are starting out with naira at the moment with plans to include more currency based on demand by the community.
    - what are the Supported Fiat payment methods?
        - Internet transfer, USSD transfer are supported at the moment, hopefully the protocol will add more payment options soon.
    - what is the ETA for Token and Fiat arrival in my wallet or bank? 
        -IFP specifies their ETA during registration, this is included when user call the endpoint
    - How can i make deposit and withdraw ?
        - User can deposits and withdraw using the stellar standardize Sep6. You can find more details here -- 
    - Do i need to register before i start using cowry protocol?
        - No, you do not need any sort of registration to start using the protocol

    - Do i need KYC to start using the protocol?
        - you do not need kyc to start using the protocol at the moment but this may change over time if the protocol signer wants it.


## DEPOSIT
- How does deposit work on cowry protocol?

    - during the deposit flow, it very simple.
    users call call the deposit endpoint as specified by sep6 and they will get an IFP account to send their deposit, once IFP acknowledge this deposit, the user Blockchain address is immediately created.

    For deposit the ETA totally depend on the how fast the user send in their deposit


- Who am i sending my Money to during deposit?
    - Deposit are made directly to a trusted IFP account. IFP are address that provide fiat liqudity and have gone through the vetting process by the protocol.
- What can i do with token received? 
    - a fully backed token with liquidity on stellar, users can swap using their favorite wallet to any token of their choice or directly to usdc and forward to exchange like stellarx stellarterm or binance.

- What are the fees for deposit on cowry protocol?
    - To encourage more liquidity providers(IFP) on the protocol, the protocol charges fee for it deposit and the fees is decided by the signers of the protocol

- How can I get in touch if there’s any problem with my deposit?
    - During your deposit, you get details about the IFP processing your transaction including their phone number you can always reach to them or reach out directly to the protocol admins via support@cowryprotocol.io
- How does the protocol resolve dispute?
    -At the moment this is done manually by reaching out to the protocol admin, the protocol assigns trusted IFPs to your case and this will be resolve in 24hrs


How do i become an IFP?
    - Becoming an IFP is striaghtforward, visit the app and connect your wallet to start the less than 1min onboarding process
What do i need to become an IFP?
    - You need a stellar address address, a stellar wallet that support wallet connect and the amount to you plan to stake to the protocol

How long does it take to after staking to get minting right?
    - This is an automatic process and is subject to when the onboarding process is completed
What happen to the Token I Staked as an IFP?
    - USDC staked during the onboarding process are fully intact and will be return back infull once the IFP decide to leave the protocol. address that manage the staked USDC is control by a multisig(all withdrawals from the address are subject at least 70% approval before withdrawals are submitted to the blockchain)
Do i get any incentise for becomeing an IFP?
    - For now IFP earn fees from deposits and withdrawals they process, this very is a flat rate at the moment but with joint approval of IFPs on the protocol we plan to introduce a tiered fee later in the future
Can i leave the protocol anytime ?
    -IFPs are perminted to leave the protocol anytime provided the IFP no longer holds any fiat in their bank account
Can my staked Token reduced for any reason?
    - Yes, if an IFP is found to be fradulent within the protocol, this might affect the staked token and also reduced their minting right.
What is my fiat_to_hold_ratio?
    - This is the maximum amount a merchant address is authorized to hold at a given time, this is managed by the protocol.

What rate is used to decide my fiat_to_hold_ratio?
I can see some tokens on my address, what are those tokens?
    - during the onboarding process, IFPs receive two token which are discussed HERE

PROTOCOL TOKENS
    - The protocol tokens are made up of three main tokens

- What is the role of NGNALLOW
- What is the role NGNLINCESE
- What is the role of NGN


The license token will serve the purpose as it name, it will only be issued to MAs with the main purpose of onchain License, this token will be the token that tells the public and the protocol how much stablecoin an address can mint and how much fiat the address is authorized to hold in their bank account, This token can only be transfer under Authorization from the Protocol, and it transfer life-cycle will likely be twice per address, 1. When an address becomes a Merchants they get the token 2. when an address withdraw their stake, the The token is burn by transfer back to the issuer address. This will be a highly restricted token and will only be transfer under the issuer or a delegated signer authority, some of stellar features to use include;


