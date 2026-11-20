//! Read access to wheel and sdist zip archives.

use std::io::Read;
use std::path::Path;

use rawzip::{CompressionMethod, FileReader, RECOMMENDED_BUFFER_SIZE, ZipArchive, ZipArchiveEntryWayfinder};

#[derive(Debug)]
pub struct ArchiveError(String);

impl std::fmt::Display for ArchiveError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::error::Error for ArchiveError {}

fn error(value: impl std::fmt::Display) -> ArchiveError {
    ArchiveError(value.to_string())
}

/// The most `read` returns for one member. Every caller reads package metadata, `RECORD` or a
/// `setup.py`; larger members go through `stream`.
const MEMBER_READ_LIMIT: u64 = 64 * 1024 * 1024;

/// The most the members of one archive may declare in total. Deflate expands about a thousand to
/// one, so the compressed download limit alone does not bound what an archive holds.
const UNPACKED_LIMIT: u64 = 4 * 1024 * 1024 * 1024;

struct Member {
    name: String,
    wayfinder: ZipArchiveEntryWayfinder,
    method: CompressionMethod,
    mode: u32,
    size: u64,
}

/// A zip archive whose central directory has been read, with members in archive order.
pub struct Archive {
    archive: ZipArchive<FileReader>,
    members: Vec<Member>,
}

impl Archive {
    pub fn open(path: &Path) -> Result<Self, ArchiveError> {
        Self::open_with_limit(path, UNPACKED_LIMIT)
    }

    fn open_with_limit(path: &Path, unpacked_limit: u64) -> Result<Self, ArchiveError> {
        let file = std::fs::File::open(path).map_err(error)?;
        let mut buffer = vec![0u8; RECOMMENDED_BUFFER_SIZE];
        let archive = ZipArchive::from_file(file, &mut buffer).map_err(error)?;
        let mut members = Vec::new();
        let mut unpacked: u64 = 0;
        {
            let mut entries = archive.entries(&mut buffer);
            while let Some(entry) = entries.next_entry().map_err(error)? {
                let name = std::str::from_utf8(entry.file_path().as_bytes())
                    .map_err(|_| ArchiveError("archive member name is not valid UTF-8".to_string()))?
                    .to_string();
                members.push(Member {
                    name,
                    wayfinder: entry.wayfinder(),
                    method: entry.compression_method(),
                    mode: entry.mode().value(),
                    size: entry.uncompressed_size_hint(),
                });
                unpacked = unpacked.saturating_add(entry.uncompressed_size_hint());
                if unpacked > unpacked_limit {
                    return Err(ArchiveError(format!("archive members expand beyond {unpacked_limit} bytes")));
                }
            }
        }
        Ok(Self { archive, members })
    }

    pub fn names(&self) -> impl Iterator<Item = &str> {
        self.members.iter().map(|member| member.name.as_str())
    }

    /// The member's mode with Unix file type bits (`0o170000`); untyped entries read as regular files.
    pub fn mode(&self, name: &str) -> Result<u32, ArchiveError> {
        Ok(self.member(name)?.mode)
    }

    /// The member's uncompressed size as recorded in the central directory.
    pub fn size(&self, name: &str) -> Result<u64, ArchiveError> {
        Ok(self.member(name)?.size)
    }

    /// Reads the whole member, verifying its size and CRC. Members above the metadata limit fail;
    /// use `stream` for those.
    pub fn read(&self, name: &str) -> Result<Vec<u8>, ArchiveError> {
        if self.member(name)?.size > MEMBER_READ_LIMIT {
            return Err(ArchiveError(format!("member {name} is larger than {MEMBER_READ_LIMIT} bytes")));
        }
        let mut out = Vec::new();
        self.reader(name)?.take(MEMBER_READ_LIMIT + 1).read_to_end(&mut out).map_err(error)?;
        if out.len() as u64 > MEMBER_READ_LIMIT {
            return Err(ArchiveError(format!("member {name} is larger than {MEMBER_READ_LIMIT} bytes")));
        }
        Ok(out)
    }

    /// Passes the member to `sink` in chunks, verifying its size and CRC, and returns its length.
    /// Reading stops with an error if the data outgrows the size the archive records.
    pub fn stream(&self, name: &str, mut sink: impl FnMut(&[u8])) -> Result<u64, ArchiveError> {
        let size = self.member(name)?.size;
        let mut reader = self.reader(name)?.take(size.saturating_add(1));
        let mut buffer = [0u8; 64 * 1024];
        let mut total: u64 = 0;
        loop {
            let read = reader.read(&mut buffer).map_err(error)?;
            if read == 0 {
                return Ok(total);
            }
            total += read as u64;
            if total > size {
                return Err(ArchiveError(format!("member {name} is larger than the {size} bytes it records")));
            }
            sink(&buffer[..read]);
        }
    }

    /// Reads at most `limit` decompressed bytes of the member.
    pub fn read_prefix(&self, name: &str, limit: u64) -> Result<Vec<u8>, ArchiveError> {
        let mut out = Vec::new();
        self.reader(name)?.take(limit).read_to_end(&mut out).map_err(error)?;
        Ok(out)
    }

    fn member(&self, name: &str) -> Result<&Member, ArchiveError> {
        self.members
            .iter()
            .find(|member| member.name == name)
            .ok_or_else(|| ArchiveError(format!("archive has no member {name}")))
    }

    fn reader(&self, name: &str) -> Result<Box<dyn Read + '_>, ArchiveError> {
        let member = self.member(name)?;
        let entry = self.archive.get_entry(member.wayfinder).map_err(error)?;
        let raw = entry.reader();
        match member.method {
            CompressionMethod::STORE => Ok(Box::new(entry.verifying_reader(raw))),
            CompressionMethod::DEFLATE => {
                Ok(Box::new(entry.verifying_reader(flate2::read::DeflateDecoder::new(raw))))
            }
            method => Err(ArchiveError(format!("member {name} uses unsupported compression method {method:?}"))),
        }
    }
}

#[cfg(test)]
pub(crate) mod testing {
    use std::io::Write;
    use std::path::Path;

    /// Writes deflate-compressed regular files, or symbolic links when `mode` is a symlink mode.
    pub(crate) fn write_archive(path: &Path, members: &[(&str, &[u8], u32)]) {
        let file = std::fs::File::create(path).unwrap();
        let mut archive = rawzip::ZipArchiveWriter::new(file);
        for (name, data, mode) in members {
            let (mut entry, config) = archive
                .new_file(*name)
                .compression_method(rawzip::CompressionMethod::DEFLATE)
                .unix_permissions(*mode)
                .start()
                .unwrap();
            let encoder = flate2::write::DeflateEncoder::new(&mut entry, flate2::Compression::default());
            let mut writer = config.wrap(encoder);
            writer.write_all(data).unwrap();
            let (encoder, descriptor) = writer.finish().unwrap();
            encoder.finish().unwrap();
            entry.finish(descriptor).unwrap();
        }
        archive.finish().unwrap();
    }

    pub(crate) fn write_files(path: &Path, members: &[(&str, &[u8])]) {
        let regular: Vec<(&str, &[u8], u32)> = members.iter().map(|(name, data)| (*name, *data, 0o100644)).collect();
        write_archive(path, &regular);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_members_in_order_with_their_file_types() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("a.whl");
        testing::write_archive(
            &path,
            &[("pkg/__init__.py", b"x = 1\n", 0o100644), ("pkg/link", b"target", 0o120777)],
        );

        let archive = Archive::open(&path).unwrap();

        assert_eq!(archive.names().collect::<Vec<_>>(), ["pkg/__init__.py", "pkg/link"]);
        assert_eq!(archive.mode("pkg/link").unwrap() & 0o170000, 0o120000);
        assert_eq!(archive.mode("pkg/__init__.py").unwrap() & 0o170000, 0o100000);
        assert_eq!(archive.read("pkg/__init__.py").unwrap(), b"x = 1\n");
        assert_eq!(archive.read_prefix("pkg/__init__.py", 2).unwrap(), b"x ");
        assert_eq!(archive.size("pkg/__init__.py").unwrap(), 6);
        assert!(archive.read("pkg/missing").is_err());
    }

    #[test]
    fn read_refuses_a_member_larger_than_a_metadata_file_can_be() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("a.whl");
        let big = vec![0u8; 65 * 1024 * 1024];
        testing::write_files(&path, &[("pkg/big.bin", &big), ("pkg/small", b"ok")]);

        let archive = Archive::open(&path).unwrap();

        assert!(archive.read("pkg/big.bin").is_err());
        assert_eq!(archive.read("pkg/small").unwrap(), b"ok");
    }

    #[test]
    fn stream_hands_over_a_member_larger_than_the_read_limit() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("a.whl");
        let big = vec![7u8; 65 * 1024 * 1024];
        testing::write_files(&path, &[("pkg/big.bin", &big)]);
        let archive = Archive::open(&path).unwrap();

        let mut seen: u64 = 0;
        let length = archive.stream("pkg/big.bin", |chunk| seen += chunk.len() as u64).unwrap();

        assert_eq!((length, seen), (big.len() as u64, big.len() as u64));
    }

    #[test]
    fn open_refuses_an_archive_whose_members_declare_more_than_the_limit() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("a.whl");
        testing::write_files(&path, &[("pkg/a", &[0u8; 600]), ("pkg/b", &[0u8; 600])]);

        assert!(Archive::open_with_limit(&path, 1199).is_err());
        assert!(Archive::open_with_limit(&path, 1200).is_ok());
    }

    #[test]
    fn rejects_a_file_that_is_not_an_archive() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("a.whl");
        std::fs::write(&path, b"not a zip").unwrap();
        assert!(Archive::open(&path).is_err());
    }
}
