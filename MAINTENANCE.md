# Maintenance

The research owner's existing recurring research task maintains this publication at meaningful milestones. Hardware research and publication are separate operations; this repository is the curated public record.

1. Read the latest local research checkpoint and check which observations or static findings actually changed.
2. Update the appropriate technical note, structured extract and[CHANGELOG](CHANGELOG.md). Preserve earlier negative results and correct mistakes openly.
3. Publish only deliberate technical fields. Exclude credentials, access material, network addresses, internal host/VM identifiers, private paths, serials/UUIDs, raw logs and proprietary firmware binaries. Follow[AGENTS.md](AGENTS.md).
4. Run `python scripts/validate_publication.py`, inspect the exact diff and staged file list, then commit and push the bounded update to this repository. Fetch first when a remote already exists; preserve others' work and never force-push as routine maintenance.
5. Record the public URL, branch and commit in the private research checkpoint. If publication fails, retain the prepared local commit and failure reason for the next run.

A recurring wake-up is not a reason to create an empty commit. Unchanged scans and repeated checks do not become new results. An unexecuted proposal stays labelled as such. Publication errors should not erase or halt useful offline research.

The GitHub history provides the public update record. No extra reminder or notification schedule is created for routine repository synchronization.
