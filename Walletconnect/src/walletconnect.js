import { isConnected } from "@stellar/freighter-api"
  import {
    StellarWalletsKit,
    WalletNetwork,
    WalletType,
  } from "stellar-wallets-kit";





async function WalletConnectTest(event) {
  if (event.type === 'click') {
    console.log(window.freighter);
    const kit = new StellarWalletsKit({
      network: WalletNetwork.PUBLIC,
      selectedWallet: WalletType.RABET,
    });
    const publicKey = await kit.getPublicKey();

    console.log(kit)
    console.log(publicKey)

    const signtx = await kit.sign({
      xdr: "AAAAAgAAAAAIBIMxkJMZ48FNWgMkSEUVnHngK7DjsSyXHDBNuU9dlQAACeoCAjeOAAAAAQAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAQAAAAAIBIMxkJMZ48FNWgMkSEUVnHngK7DjsSyXHDBNuU9dlQAAAAAAAAAAAmJaAAAAAAAAAAAA",
      publicKey:publicKey
    });

    console.log(signtx)
  }

  }


async function OpenWalletConnect() {
  console.log("wallet connect is ready")
  const kit = new StellarWalletsKit({
     network: WalletNetwork.PUBLIC,
     selectedWallet: WalletType.RABET,
   });
   console.log(kit)
  const publicKey = await kit.getPublicKey();
  console.log(publicKey)
  const checkConnect = await kit.startWalletConnect({
    name: "LocalHost",
    description: "This is just a test",
    url: "http://localhost:3000/",
    icons: "",
    projectId: "7332361201b4edd62c4f97837b648413",
  });

  console.log(checkConnect)
  const contt = await this.walletService.kit.connectWalletConnect();
  console.log(contt)
  
}
  // return "this is just some random jokes";


export {WalletConnectTest, OpenWalletConnect};
