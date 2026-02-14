require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

// Load from .env — add these to your .env file:
//   AMOY_RPC_URL=https://rpc-amoy.polygon.technology
//   DEPLOYER_PRIVATE_KEY=0xYourPrivateKeyHere
//   POLYGONSCAN_API_KEY=YourPolygonscanApiKey (optional, for verification)

const AMOY_RPC = process.env.AMOY_RPC_URL || "https://rpc-amoy.polygon.technology";
const DEPLOYER_KEY = process.env.DEPLOYER_PRIVATE_KEY || "0x0000000000000000000000000000000000000000000000000000000000000001";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },

  networks: {
    hardhat: {},

    amoy: {
      url: AMOY_RPC,
      chainId: 80002,
      accounts: [DEPLOYER_KEY],
      gasPrice: "auto",
    },
  },

  etherscan: {
    apiKey: {
      polygonAmoy: process.env.POLYGONSCAN_API_KEY || "",
    },
  },

  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};
