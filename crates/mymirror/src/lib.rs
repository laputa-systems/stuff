#![forbid(unsafe_code)]

pub mod error;
mod acquire;
mod archive;
mod build;
mod glob;
mod json;
pub mod manifest;
mod tar_xz;

pub use acquire::{fetch_verified, Acquire, HttpsAcquire, sha256_hex};
pub use build::{
    BuiltArtifact, BuiltMirror, REGISTRY, RENDERER_VERSION, SCHEMA_VERSION, assemble, build,
    generation_id, normalize_base_url,
};
pub use error::{Error, Result};
