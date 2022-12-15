import { WalletConnectTest, OpenWalletConnect } from "./walletconnect";
import logo from './assets/logo.png'


// const logoImg = document.getElementById("logoImg"); way to get an html id and attach an attribute to it from js
// logoImg.src = logo

const clicked = document.getElementById("newsbtn");
const WCBTN = document.getElementById("walletconnect");

clicked.addEventListener('click', WalletConnectTest) 
WCBTN.addEventListener("click", OpenWalletConnect);

// WalletConnectTest();
// console.log("this is a test")