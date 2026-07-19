# Release checklist

## Blocking gates

- [ ] Obtain a signed speaker voice/data release.
- [ ] Record attribution preference and permitted uses.
- [ ] Define withdrawal and version-retirement procedures.
- [ ] Select an explicit dataset license covering audio and metadata.
- [x] Verify that every distributed audio file matches the manifest checksum.
- [x] Remove source filenames and private filesystem information from public metadata.
- [ ] Complete a privacy and misuse review, including voice-cloning risks.
- [ ] Add a model-training use statement and downstream redistribution terms.
- [ ] Assign a versioned citation and persistent release identifier.

## Annotation gates

- [x] Verify all utterance transcripts and naturalness.
- [x] Record corrections and quality status.
- [x] Freeze contrast groups and benchmark identifiers.
- [x] Remove unverified meaning-risk weights from the required training contract.
- [ ] Define and human-verify a versioned Yoruba phoneme inventory and G2P output.
- [ ] Verify word/syllable/vowel boundaries for controlled contrast items.
- [ ] Distinguish orthographic from context-conditioned surface tone.

## Training-readiness gates

- [x] Mark the existing 120 evaluated prompts as benchmark-excluded diagnostic data.
- [ ] Collect or designate leakage-safe train, development, and concealed test material.
- [x] Add stable audio checksums to every released record.
- [ ] Audit phoneme, syllable, tone-sequence, and lexical coverage.
- [ ] Add multiple speakers and reserve complete speakers for generalization testing.
- [x] Run automated schema, Unicode, audio, split, and duplicate checks on the release candidate.
- [ ] Complete fluent review of all final test pronunciation annotations.

Audio must remain outside the public repository until every blocking release gate is satisfied.

The draft agreement, plain-language summary, and unsigned release record are in `governance/`. A conversational statement of permission does not change the release record to signed.
