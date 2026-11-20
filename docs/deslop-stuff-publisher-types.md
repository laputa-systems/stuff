# Publisher type profile

Scope: `crates/stuff/src` at DSLP-10's base. The crate has 21,031 Rust source lines including unit tests. The production measurement used `cargo clippy --offline -p stuff --lib --bins --message-format=json` with each candidate enabled using `-W`. Counts below include diagnostics whose first span is under `crates/stuff/src`; dependency diagnostics are excluded. The command exited 0. The compiler was rustc 1.102.0-nightly (5b7b37ae 2026-11-08).

| Candidate | Diagnostics | Decision |
| --- | ---: | --- |
| `unsafe_code = forbid` | 0 | Already enforced by the library and binary crate roots; no new setting. |
| `wildcard_enum_match_arm` | 5 | Reject: no demonstrated defect or deleted escape hatch. The matches include open-ended value kinds. |
| `match_wildcard_for_single_variants` | 0 | Reject: no witness. |
| `cast_possible_truncation` | 11 | Reject: no demonstrated defect. Examples include bounded wire reads and range-checked Cargo index versions; some warnings concern 32-bit targets. |
| `cast_sign_loss` | 3 | Reject: no demonstrated defect. The index conversion checks nonnegative values and the date conversions follow bounded calendar arithmetic. |
| `unwrap_used` outside tests | 2 | Reject: no defect witness. The CLI lookup and help footer rely on internal tables. |
| `expect_used` outside tests | 14 | Reject: no defect witness. Several format into `String` or construct HMAC with a key length the implementation accepts. |
| `redundant_clone` | 14 | Reject: ownership suggestions do not reject an invalid type or remove a typing escape hatch. |
| `needless_pass_by_value` | 18 | Reject: ownership suggestions do not reject an invalid type or remove a typing escape hatch. |

No new profile setting was adopted. No typing change met the required witness or deleted-trust test. Existing checked conversions and internal assertions remain. The source escape-hatch search from the deslop tool reference counted 331 matching lines before and after; that count includes unit tests and occurrences in error strings, and is not a count of unsound operations. No public contract or runtime behavior changed.
