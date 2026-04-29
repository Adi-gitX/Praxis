import { expect } from "chai";
import { ethers } from "hardhat";

describe("Praxis primitives", () => {
  it("EmergencyPause: guardian halts; unhalt requires schedule + delay", async () => {
    const [admin, guardian] = await ethers.getSigners();
    const Pause = await ethers.getContractFactory("EmergencyPause");
    const pause = await Pause.deploy(admin.address, guardian.address, 60 * 60);
    await pause.waitForDeployment();

    expect(await pause.isHalted()).to.equal(false);
    await pause.connect(guardian).halt("test");
    expect(await pause.isHalted()).to.equal(true);

    await expect(pause.connect(admin).unhalt()).to.be.revertedWithCustomError(
      pause,
      "UnhaltNotScheduled"
    );

    await pause.connect(admin).scheduleUnhalt();
    await expect(pause.connect(admin).unhalt()).to.be.revertedWithCustomError(
      pause,
      "UnhaltNotReady"
    );
  });

  it("StrategyRegistry: register, trip, isApproved", async () => {
    const Reg = await ethers.getContractFactory("StrategyRegistry");
    const reg = await Reg.deploy();
    await reg.waitForDeployment();

    const tx = await reg.register(
      ethers.encodeBytes32String("trend_following"),
      ethers.Wallet.createRandom().address,
      ethers.parseEther("100")
    );
    await tx.wait();

    expect(await reg.isApproved(1, ethers.parseEther("50"))).to.equal(true);
    expect(await reg.isApproved(1, ethers.parseEther("200"))).to.equal(false);

    await reg.trip(1, "drawdown breach");
    expect(await reg.isApproved(1, ethers.parseEther("50"))).to.equal(false);
  });
});
