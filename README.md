# DFNF Bruma 2 Patch

Local and private, never published: DFNF - Bruma.esp with the records removed that Beyond Skyrim - Bruma 2.0.0 and
Beyond Skyrim - Assets SE 2026.11.11 no longer contain.

Source: DFNF - Default Face NPCs Fixed 1.25, Nexus Mods 54515, by AndrealletiusVIII and UnknownG12.
Change: 40 NPC_ override records removed (records that Beyond Skyrim - Bruma 2.0.0 and Assets SE no longer contain) and the BS_DLC_patch.esp master removed.

A record is dangling when it overrides a `BSHeartland.esm` or `BSAssets.esm` record whose object ID is absent from the 2.0
plugins. The EditorIDs of the removed records are in neither plugin, so nothing is remapped.

## Build

    python3 build.py          # dry run, writes build/review.txt
    python3 build.py --write  # serialize with Spriggit, remove, deserialize to dist/, verify

Inputs (`inputs/`, pinned by `inputs.sha256`, not committed): the plugin from the installed mod, `BSHeartland.esm` from
Bruma 2.0.0 and `BSAssets.esm` from Assets SE 2026.11.11. Needs the Skyrim AI toolkit's `tools/spriggit-cli.sh`
(`SKYRIM_TOOLKIT` overrides its path).

## Verification

The write pass fails unless the kept FormKeys equal the output's, no output record overrides a missing record, any
dropped master is gone, and every kept record equals its input after the normalisations Spriggit makes on any round trip
(list subrecords and VMAD properties reordered, NPC_ `DNAM` padding bytes, the last bit of `QNAM` floats). Header flags
(ESL) and version are unchanged.

## Install

Copy `dist/DFNF - Bruma.esp` over the original in MO2. Reinstalling the source mod restores the original.
