# Correct two Germanium reaction equations to match Filella & May Table 6

The Germanium reference page currently omits four reactant protons in its Ge(IV)/Ge(II) reaction and gives the difluorohydroxo product a negative rather than positive charge. These transcriptions are unbalanced and cause PHREEQC to reject the corresponding input. Restore `+ 4 H+` in the first equation and change `GeF2(OH)-` to `GeF2(OH)+` in the last equation, matching Table 6 of Filella & May (2023), DOI [10.1016/j.apgeochem.2023.105631](https://doi.org/10.1016/j.apgeochem.2023.105631). All log K values stay unchanged.

Validation: two separate comparisons checked the equations with the published Table 6; exact atom/charge checks pass for all 11 reactions in the corrected representation. A controlled native PHREEQC 3.7.3 run rejects the page-as-written pair and accepts the corrected pair with the same constants, base database and synthetic solution. This verifies transcription and input compatibility, not the empirical accuracy of the source recommendations.

The scientific values and recommendations are the original authors' work. Automated verification is not external expert review.

Prepared locally against commit `8ed9e849f49d1a8cfdf4b77c4bad4374d2e588a2`. Not submitted; no maintainer acceptance or permission to publish is claimed.
