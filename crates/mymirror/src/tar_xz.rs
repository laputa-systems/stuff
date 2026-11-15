use std::io::Write;

use crate::archive::{Member, MemberKind};
use crate::error::{Error, Result};

pub(crate) fn write_tar_xz(members: &[Member]) -> Result<Vec<u8>> {
    let encoder = lzma_rust2::XzWriter::new(Vec::new(), lzma_rust2::XzOptions::with_preset(9))
        .map_err(|error| Error::operation(format!("could not start xz encoder: {error}")))?;
    let mut archive = tar::Builder::new(encoder);
    for member in members {
        let mut header = tar::Header::new_gnu();
        header.set_mode(member.mode & 0o7777);
        header.set_uid(0);
        header.set_gid(0);
        header.set_mtime(0);
        match member.kind {
            MemberKind::File => {
                header.set_entry_type(tar::EntryType::file());
                header.set_size(member.data.len() as u64);
                archive.append_data(&mut header, &member.path, member.data.as_slice())
                    .map_err(|error| Error::operation(format!("could not write tar member {}: {error}", member.path)))?;
            }
            MemberKind::Symlink => {
                header.set_entry_type(tar::EntryType::symlink());
                header.set_size(0);
                #[cfg(unix)]
                let target = {
                    use std::os::unix::ffi::OsStrExt;
                    std::ffi::OsStr::from_bytes(&member.data)
                };
                #[cfg(not(unix))]
                let target = std::ffi::OsStr::new(std::str::from_utf8(&member.data)
                    .map_err(|error| Error::operation(format!("invalid link target for {}: {error}", member.path)))?);
                archive.append_link(&mut header, &member.path, target)
                    .map_err(|error| Error::operation(format!("could not write tar link {}: {error}", member.path)))?;
            }
        }
    }
    let mut encoder = archive.into_inner()
        .map_err(|error| Error::operation(format!("could not finish tar archive: {error}")))?;
    encoder.flush().map_err(|error| Error::operation(format!("could not flush xz archive: {error}")))?;
    encoder.finish().map_err(|error| Error::operation(format!("could not finish xz archive: {error}")))
}
