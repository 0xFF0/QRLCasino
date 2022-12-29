#!/bin/bash
NET_NAME=Testnet    # Mainnet/Testnet
BOOTSTRAP=false
WOOCOMMERCE_SETUP=false

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
QRL_DATA_DIR=./qrlData/$NET_NAME
BOOTSTRAP_DEST=$QRL_DATA_DIR/data
BOOTSTRAP_FILE_NAME=QRL_"$NET_NAME"_State.tar.gz
CHECKSUM_FILE="$NET_NAME"_State_Checksums.txt
BOOTSTRAP_URL=https://cdn.qrl.co.in/${NET_NAME,,}/$BOOTSTRAP_FILE_NAME
BOOTSTRAP_URL_CHECKSUM=https://cdn.qrl.co.in/${NET_NAME,,}/$CHECKSUM_FILE



# Create data folder
if [ ! -d data ]; then
  mkdir -p data
fi


# Create qrlData folder
if [ ! -d $BOOTSTRAP_DEST ]; then
  mkdir -p $BOOTSTRAP_DEST
fi

# Bootstrap parameter
if [[ $1 == --bootstrap ]]; then
    BOOTSTRAP=true
fi
if [[ $2 == --bootstrap ]]; then
    BOOTSTRAP=true
fi




# Install packages
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install docker.io docker-compose python3.8-venv python3-pip python3-wheel curl -y


# Bootstrap
if $BOOTSTRAP ; then
  DOWNLOAD_BOOTSTRAP=true
  if [ -f "$BOOTSTRAP_FILE_NAME" ]; then
    echo "$BOOTSTRAP_FILE_NAME already exists."
    read -p "Do you wish to download the bootstrap again (y/n)?" yn
    case $yn in
        [Yy]* ) rm $BOOTSTRAP_FILE_NAME; rm $CHECKSUM_FILE;;
        [Nn]* ) DOWNLOAD_BOOTSTRAP=false;;
        * ) echo "Please answer yes or no.";;
    esac
  fi

  if $DOWNLOAD_BOOTSTRAP ; then
    wget $BOOTSTRAP_URL_CHECKSUM
    wget $BOOTSTRAP_URL
	echo "SHA3-512 checksum verification started..."
    SHA3_CHECKSUM=`sed -n '/SHA3-512/{n;p}' $CHECKSUM_FILE`
    SHA3=($(openssl dgst -sha3-512 $BOOTSTRAP_FILE_NAME))
    if [ "$SHA3_CHECKSUM" = "${SHA3[1]}" ]; then
      echo "Verification ok: $SHA3_CHECKSUM ."
	  echo "Extracting bootstrap data..."
      tar -xzf $BOOTSTRAP_FILE_NAME -C $BOOTSTRAP_DEST  
    else
      echo "Bootstrap verification failed. Expected $SHA3_CHECKSUM got ${SHA3[1]}."
      exit 1
    fi
  fi
fi

# Set network type for the docker container
if [[ $NET_NAME == Mainnet ]]; then
  sed -i 's/start_qrl --network-type testnet \&/start_qrl  \&/g' dockerfiles/RunWallet.sh
  #sed -i 's/RUN pip3 install -U "qrl==3.0.1"/RUN pip3 install -U qrl/g' dockerfiles/QRL_wallet.docker
else
  #Testnet 
  #sed -i 's/RUN pip3 install -U qrl/RUN pip3 install -U "qrl==3.0.1"/g' dockerfiles/QRL_wallet.docker
  sed -i 's/start_qrl  \&/start_qrl --network-type testnet \&/g' dockerfiles/RunWallet.sh
fi

# TODO: Looks like a bug for testnet, no config.yml and genesis.yml created with root account on docker
if [[ $NET_NAME == Testnet ]]; then
  cat << EOF > $QRL_DATA_DIR/config.yml
peer_list: [ "18.130.83.207", "209.250.246.234", "136.244.104.146", "95.179.154.132" ]
genesis_prev_headerhash: 'Final Testnet'
genesis_timestamp: 1668696491
genesis_difficulty: 5000
p2p_local_port: 29000
p2p_public_port: 29000
admin_api_port: 29008
public_api_port: 19009
mining_api_port: 29007
grpc_proxy_port: 28090
wallet_daemon_port: 28091
public_api_server: "127.0.0.1:29009"
wallet_api_port: 29010
EOF
  cat << EOF > $QRL_DATA_DIR/genesis.yml
genesisBalance:
- address: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
  balance: '105000000000000000'
header:
  hashHeader: 1nZdbgr36LJbrFhyeZmeFruwvTA4RFk04tnzskqJBB4=
  hashHeaderPrev: RmluYWwgVGVzdG5ldA==
  merkleRoot: wquld1GTaqfKWRhAdWpOeREWVdCmlTYIAUrY9eWGwTQ=
  rewardBlock: '65000000000000000'
  timestampSeconds: '1668696491'
transactions:
- coinbase:
    addrTo: AQYA3oDYKOMv8cfAHpT2zewSkuiz/0gYQy5+atQfOsdD57loCQog
    amount: '65000000000000000'
  masterAddr: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
  nonce: '1'
  transactionHash: wquld1GTaqfKWRhAdWpOeREWVdCmlTYIAUrY9eWGwTQ=
EOF

fi


# QRL node configuration
cat << EOF >> $QRL_DATA_DIR/config.yml
public_api_host: '0.0.0.0'
mining_api_enabled: True
mining_api_host: '0.0.0.0'
EOF


# Python setup
pip install -r requirements.txt


# Start docker-compose
sudo docker-compose -f docker-compose-qrl-casino.yaml up -d --build


# Start casino
cd discord
python3 bot.py


