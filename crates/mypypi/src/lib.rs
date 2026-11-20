#![forbid(unsafe_code)]

pub mod acquire;
pub mod add;
pub mod build;
pub mod catalog;
pub mod cli;
pub mod config;
pub mod error;
pub mod index;
pub mod json;
pub mod models;
pub mod platforms;
pub mod planner;
pub mod process_policy;
pub mod publish;
pub mod sandbox;
pub mod store;
pub mod validate;
pub mod wheel_metadata;
mod wheel_zip;

pub(crate) fn lower_hex(bytes: impl AsRef<[u8]>) -> String {
    use std::fmt::Write as _;
    let bytes = bytes.as_ref();
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        write!(out, "{byte:02x}").expect("writing to a string cannot fail");
    }
    out
}

/// A value that differs between processes and calls, for temporary file and directory names.
pub(crate) fn unique_u64() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let nanos = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_nanos()).unwrap_or(0);
    nanos as u64 ^ (std::process::id() as u64).wrapping_mul(0x9E3779B97F4A7C15)
}
