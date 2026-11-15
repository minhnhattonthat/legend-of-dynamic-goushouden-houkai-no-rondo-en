# Skill gotchas (one line each: reference file, then the fact)

- references/graphics.md: a static sweep of a GBA game with thousands of packed blocks needs a tilemap filter (u16 entries: few high-byte values, many low-byte values); without it 6,196 of 9,645 blocks were stripe noise and the sheets ran to 97 pages.
- references/graphics.md: `codex exec -i` reviewers saw no text on full 1056 px sweep pages; cutting each page into quarters zoomed 2x fixed it, but two passes still disagreed on 45 of 167 hits and both missed one block found by eye. Run two passes and take the union.
- references/emulator-qa.md: `codex exec -i a.png b.png "prompt"` swallows the prompt as an image path; pass images comma-separated and the prompt on stdin (`-`).
- references/pipeline.md (Recon, compression): hooking the unpacker's copy-out point (decoder done, before copy to dst) and dumping the temp buffer gave ground truth for writing two unknown codecs from disassembly; both matched on the first test run.
- references/pipeline.md (Recon, compression): a codec may read before the start of its output buffer (this game's type 3 expects zeros there); a decoder that raises on such a back-reference rejects real blocks.
