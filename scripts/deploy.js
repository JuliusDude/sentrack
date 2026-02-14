const hre = require("hardhat");

async function main() {
  console.log("━".repeat(50));
  console.log("Deploying CommunitySentimentOracle...");
  console.log("Network:", hre.network.name);
  console.log("━".repeat(50));

  const [deployer] = await hre.ethers.getSigners();
  console.log("Deployer:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Balance:", hre.ethers.formatEther(balance), "POL");

  if (balance === 0n) {
    throw new Error("Deployer has 0 balance. Get testnet POL from https://faucet.polygon.technology/");
  }

  // Deploy
  const Oracle = await hre.ethers.getContractFactory("CommunitySentimentOracle");
  const oracle = await Oracle.deploy();
  await oracle.waitForDeployment();

  const address = await oracle.getAddress();

  console.log("\n✅ CommunitySentimentOracle deployed!");
  console.log("   Address:", address);
  console.log("   Explorer: https://amoy.polygonscan.com/address/" + address);
  console.log("\n📋 Paste this address into SenTrack when prompted.");
  console.log("━".repeat(50));

  // Optional: verify on Polygonscan
  if (hre.network.name === "amoy" && process.env.POLYGONSCAN_API_KEY) {
    console.log("\nWaiting 30s for Polygonscan indexing...");
    await new Promise((r) => setTimeout(r, 30000));

    try {
      await hre.run("verify:verify", {
        address: address,
        constructorArguments: [],
      });
      console.log("✅ Contract verified on Polygonscan!");
    } catch (e) {
      console.log("⚠️  Verification failed (non-fatal):", e.message);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Deploy failed:", error);
    process.exit(1);
  });
