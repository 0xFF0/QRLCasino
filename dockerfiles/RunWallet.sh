#!/bin/bash

echo Starting wallet
start_qrl --network-type testnet &
qrl_walletd 
$HOME/go/bin/walletd-rest-proxy -serverIPPort 0.0.0.0:5359 -walletServiceEndpoint 127.0.0.1:19010

