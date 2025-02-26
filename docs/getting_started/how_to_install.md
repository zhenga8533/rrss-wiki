# How To Install

---

## Introduction

Welcome to Rising Ruby and Sinking Sapphire!

There are two recommend ways to play this mod.

- The first is to use a 3DS with the Luma3DS custom firmware installed. Instructions to install CFW on a 3DS can be found at https://3ds.hacks.guide/.
- The second is to use Citra, a 3DS emulator. A download can be found on Citra's official site at https://citra-emu.org/. The Nightly build is OK. I'll only be going over the Windows PC version in this guide (but some instructions may apply to other platforms anyway).

---

## Prerequisites

There are two important prerequisites:

1. **You must already be able to play Omega Ruby or Alpha Sapphire on whichever platform you choose.**

If playing on an actual 3DS and you have either an OR/AS cart or an OR/AS eShop download, that should suffice.
Otherwise, you'll need to figure out how to get ahold of the base game for the platform you choose.
Instructions to do that will not be provided here but can likely be found online via forums or YouTube.

2. **You cannot have any of the eShop patches for Omega Ruby or Alpha Sapphire installed.**

Rising Ruby and Sinking Sapphire only currently work on v1.0 of OR/AS.
If you try to run it with an update installed, the best case scenario is that some changes to the game won't apply (Poké Mart items and text edits), and the worst case is that the game just won't boot up.
This is something that may be fixed in the future as other mods of OR/AS do work fine on v1.4.

On a 3DS, you can delete an installed update by going to System Settings > Data Management > Nintendo 3DS > Downloadable Content, finding the OR/AS patch and deleting it.
On Citra, you can delete an installed update by right-clicking the game on your Citra's game list, selecting "Open Update Data", then going up two levels to the /00040000e/ folder and deleting the /0011c400/ (Omega Ruby) or /0011c500/ (Alpha Sapphire) folders.

If you require extra assistance, Dio Vento's Rutile Ruby and Star Sapphire mod has instructions that go into a lot more detail on getting this beginning part set up.
You can find that here (and also play that, if you wish!): https://diovento.wordpress.com/rrss/

---

## Installing on a 3DS

Assuming that you already have Luma CFW installed after following the 3ds.hacks.guide tutorial and that you've fulfilled the prerequisites above:

1. Enable Game Patching

- When booting the 3DS, hold down the SELECT button. This should bring up a Luma settings menu including an item named "Enable Game Patching". Make sure this is ticked, then press START to save the setting and boot as normal.
- You should only need to do this once. If you're confident that this is already enabled, then you can skip this step.

2. Load File Content

- Load up your SD card on your computer (or some other way so you can access the file system there).
- At the root of the SD card, if you don't already have one, create a folder called "luma". Then inside the "luma" folder, create a folder called "titles".
- Inside "titles", create a new folder called "000400000011c400" if you want to play Rising Ruby or "000400000011c500" if you want to play Sinking Sapphire. (These correspond to the Title IDs of Omega Ruby and Alpha Sapphire respectively!)
- In your download of Rising Ruby or Sinking Sapphire, there should be a folder called "Files", and inside that a folder called "Main Files".
- Copy the contents of the "Main Files" folder into the "000400000011c400" or "000400000011c500" folder you just made.
- Optionally, remove or replace any files if you want to adjust the default experience to something a bit more vanilla (consult the "FileList.txt" inside the "Files" folder for more info).

3. Verify Install

- Put your SD card back into your 3DS, boot it up, then load your Omega Ruby or Alpha Sapphire.
- If you've done everything correctly then you should see that the title screen has a new logo. If that's worked, you're good to go!
- If you're positive you've done everything written above and are still having issues, you can drop me a message at @Drayano60 on Twitter and I'll try and assist you.

Note about saves:

- It's worth mentioning that your 3DS only stores the one save file for Omega Ruby or Alpha Sapphire.
- If you have an existing save, you can delete it via the 3DS's settings menu or by pressing B, X and Up at the same time on the title screen, but you may want to backup your save first before doing so.
- You can do this using a 3DS app called JKSM, which you can get from the Releases tab here: https://github.com/J-D-K/JKSM. This will also allow you to restore it at a later date.

If you want to disable the mod, either remove the files from your SD card (you can just delete the "000400000011c400" or "000400000011c500" folder) or hold down SELECT when booting the 3DS up and disable "Enable Game Patching".

# Installing on Citra

Assuming that you already have Omega Ruby or Alpha Sapphire listed in your Citra's game list and that you've fulfilled the prerequisites above:

1. Open Mod Location

- On the game list, right-click your Omega Ruby or Alpha Sapphire and select "Open Mods Location".
- This should open a file explorer pointed at a location ending with "/Citra/load/mods/000400000011c400 if you used Omega Ruby, or "Citra/load/mods/000400000011c500" if you used Alpha Sapphire.

2. Copy File Content

- In your download of Rising Ruby or Sinking Sapphire, there should be a folder called "Files", and inside that a folder called "Main Files".
- Copy the contents of the "Main Files" folder into the "000400000011c400" or "000400000011c500" folder that Citra just opened for you.
- Optionally, remove or replace any files if you want to adjust the default experience to something a bit more vanilla (consult the "FileList.txt" inside the "Files" folder for more info).

3. Verify Install

- Double click the game on Citra to boot it up.
- If you've done everything correctly, then you should see that the title screen has a new logo. If that's worked, you're good to go!
- You may also find that the next time you open Citra, the game list will have changed to say "Pokémon Sinking Sapphire" or "Pokémon Rising Ruby" instead.
- If you're positive you've done everything written above and are still having issues, you can drop me a message at @Drayano60 on Twitter and I'll try and assist you.

Note about saves:

- It's worth mentioning that Citra only stores the one save file for Omega Ruby or Alpha Sapphire.
- If you have an existing save, you can find your save data on Citra by right-clicking either Omega Ruby or Alpha Sapphire and selecting "Open Save Data".
- This should open a folder that contains a file called "main". Remove this somehow (either delete it or cut and paste it elsewhere) and then the game should no longer have a save when you boot it up.
