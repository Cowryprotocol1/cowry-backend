# PROTOCOL GUILD

### Objective
- To provide a general overview of how the protocol works and how users funds are secure, How Merchants are onboard and many more details


### TO DO

- merchant onboarding to be Manuel and subjected to approval from other merchant

<!-- Market Risk -->

An IFP staked $100 at an exchange rate of 500
They get minting right of 40,000 which is 80%
Tomorrow the exchange goes becomes 250
And IFP has the 40000 in their account
    If they continue with the protocol, when they want to offboard their 100 will now become 25000 with the present market value
        - Volatility is always something that is here to stay
        - Most IFPs wont care about this, they care about mak
What is stopping an IFP from keeping the 40,000 and just leaving the protocol with $100 that can now only be converted to 25000 instead of the intital 40000

<!-- Possible Solution -->
- Reduce Minting right(50 - 60 %)
- Provide a quick way for IFPs to be able to offload their risk to the protocol maybe by selling their staked token to the protocol reserve pool at a certain rate
- Liquidation of IFP staked tokens if price fall under certain price range(maybe 10% for stablecoin like usdc)
 



 ============================================

 The AUDIT Endpoint
 - endpoint should return total stablecoin
 - endpoint should return total allowed token
 - endpoint should return total license token
 - List of available IFPs {
    their staked amount,
    their exchange amount,
    Numbers of allowed Token gotten
    Numbers of license Token gotten
    Total Fiat in bank Account
    blockchain Address onchain
    pending transaction including amount
 }
 - endpoint should return total stablecoin
 - Total fiat held in all IFPs account
 <!-- this should be equal to the total supply of the token -->
 - 