# Maintaining the notebook and repository

## Which copy to edit

`Run_FLake.ipynb` in this repository is the shared tutorial. The README's Colab button opens that notebook. The earlier Drive notebook can remain a working copy, but repository changes are the ones reached through the public button.

In Colab, use **File → Save a copy in GitHub** to save an edited notebook to this repository and branch. Saving to Drive creates a separate copy. A running Colab session does not automatically reload later commits: reopen the GitHub notebook link in a fresh runtime to test an update. The setup cell loads the configured GitHub branch.

For a substantial change, use a separate branch and review it before updating `main`. README text and other small files can be edited on GitHub. Keep the original attribution in `physics.py` and `NOTICE.md`.

## What needs checking

Writing, titles, colours and the default lake can be changed independently of the numerical model. For a different default example, update `default_lake_id` in `example_settings.json` and replace the saved preview images and notebook introduction to match. Use a lake ID already in `data/lakes.csv`.

The ten original Python modules match the verified MSI package. Their hashes are recorded in `verification/model_code_sha256.json`. This publication adds data retrieval and changes notebook setup; it does not change those modules. If you later change numerical integration, physics, forcing, restarts or input handling, recheck the affected runs before describing the modified version as reproducing the production implementation.

## Example data

The large original `FLake_Tutorial.zip` is an asset on release `data-v1.0.0`. `example_data.json` records its URL and all expected data paths and byte sizes. The downloader checks the ZIP's data entries and CRCs and verifies that its lake catalogue matches the repository. Only data files are installed; code inside the ZIP is not installed.

Keep a released dataset fixed. If the scientific inputs change, attach a newly versioned archive and update the manifest and applicable verification records together. A SHA-256 archive digest can also be added as the `sha256` field in `example_data.json`; the downloader will enforce it when present. Do not invent an archive digest.

## Before a public update

Open the GitHub notebook in a fresh Colab runtime. Check the default historical example, one SSP continuation, the two-lake figures and observation display. Make sure the release download and README images resolve. Preserve a usable dataset URL when changing repository names or ownership.
