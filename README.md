# DFNF Bruma 2 Patch

DFNF - Bruma.esp with the records removed that Beyond Skyrim - Bruma 2.0.0 and
Beyond Skyrim - Assets SE 2026.11.11 no longer contain.

Source: DFNF - Default Face NPCs Fixed 1.25, Nexus Mods 54515, by AndrealletiusVIII and UnknownG12.
Change: 40 NPC_ override records removed (records that Beyond Skyrim - Bruma 2.0.0 and Assets SE no longer contain) and the BS_DLC_patch.esp master removed.

A record is dangling when it overrides a `BSHeartland.esm` or `BSAssets.esm` record whose object ID is absent from the 2.0
plugins. The EditorIDs of the removed records are in neither plugin, so nothing is remapped.

## Build

    python3 build.py          # dry run, writes build/review.txt
    python3 build.py --write  # serialize with Spriggit, remove, deserialize to dist/, verify

Inputs (`inputs/`, pinned by `inputs.sha256`, not committed): the plugin from the installed mod, `BSHeartland.esm` from
Bruma 2.0.0 and `BSAssets.esm` from Assets SE 2026.11.11. Needs `tools/spriggit-cli.sh` from the [Skyrim AI toolkit](https://github.com/kxgcayh/skyrim-agents-toolkit): clone it next to this repo
(or next to a parent folder), or set `SKYRIM_TOOLKIT` to its folder.

## Verification

The write pass fails unless the kept FormKeys equal the output's, no output record overrides a missing record, any
dropped master is gone, and every kept record equals its input after the normalisations Spriggit makes on any round trip
(list subrecords and VMAD properties reordered, NPC_ `DNAM` padding bytes, the last bit of `QNAM` floats). Header flags
(ESL) and version are unchanged.

## Install

Copy `dist/DFNF - Bruma.esp` over the original in MO2. Reinstalling the source mod restores the original.

## Credits and Permissions

Credit goes to the authors of the mods below. Permission status is based on each mod's Nexus page permissions, read on 2026-11-11 and 2026-11-13.

- [DFNF - Default Face NPCs Fixed](https://www.nexusmods.com/skyrimspecialedition/mods/54515) by AndrealletiusVIII: allowed based on the Nexus page permissions
- [Beyond Skyrim - Bruma SE](https://www.nexusmods.com/skyrimspecialedition/mods/10917) by The Beyond Skyrim - Cyrodiil Development Team: allowed based on the Nexus page permissions
- [Beyond Skyrim - Assets SE](https://www.nexusmods.com/skyrimspecialedition/mods/198585) by BeyondSkyrimDC: allowed based on the Nexus page permissions

Credit the authors above, distribute under DFNF's license, and share fixes with the Beyond Skyrim team.

